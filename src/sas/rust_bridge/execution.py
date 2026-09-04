"""Rust-backed execution context with capability-bound access."""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from . import sas_core_py as _rust
except ImportError:
    _rust = None


class ExecutionContext:
    """Capability-bound execution context backed by Rust.
    
    Usage:
        ctx = ExecutionContext()
        ctx = ctx.with_read_filesystem().with_dispatch_network()
        if ctx.can_read_filesystem:
            # perform read
    """
    
    def __init__(self):
        if _rust is None:
            raise RuntimeError("Rust extension not available")
        self._inner = _rust.ExecutionContext()
    
    @property
    def can_read_filesystem(self) -> bool:
        return self._inner.can_read_filesystem
    
    @property
    def can_write_filesystem(self) -> bool:
        return self._inner.can_write_filesystem
    
    @property
    def can_dispatch_network(self) -> bool:
        return self._inner.can_dispatch_network
    
    @property
    def can_execute_commands(self) -> bool:
        return self._inner.can_execute_commands
    
    @property
    def can_process_payments(self) -> bool:
        return self._inner.can_process_payments
    
    def with_read_filesystem(self) -> "ExecutionContext":
        new = ExecutionContext.__new__(ExecutionContext)
        new._inner = self._inner.with_read_filesystem()
        return new
    
    def with_write_filesystem(self) -> "ExecutionContext":
        new = ExecutionContext.__new__(ExecutionContext)
        new._inner = self._inner.with_write_filesystem()
        return new
    
    def with_dispatch_network(self) -> "ExecutionContext":
        new = ExecutionContext.__new__(ExecutionContext)
        new._inner = self._inner.with_dispatch_network()
        return new
    
    def with_execute_commands(self) -> "ExecutionContext":
        new = ExecutionContext.__new__(ExecutionContext)
        new._inner = self._inner.with_execute_commands()
        return new
    
    def with_process_payments(self) -> "ExecutionContext":
        new = ExecutionContext.__new__(ExecutionContext)
        new._inner = self._inner.with_process_payments()
        return new
    
    def __repr__(self) -> str:
        return repr(self._inner)
