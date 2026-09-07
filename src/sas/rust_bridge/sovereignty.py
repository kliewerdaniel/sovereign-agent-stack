"""Rust-backed sovereignty assertions."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from . import sas_core_py as _rust
except ImportError:
    _rust = None


class SovereigntyAsserter:
    """Sovereignty assertion engine backed by Rust.
    
    Verifies that the agent stack meets sovereignty requirements.
    """
    
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
        if _rust is None:
            raise RuntimeError("Rust extension not available")
        self._inner = _rust.SovereigntyAsserter()
    
    def with_layer(self, layer: str, ownership: str) -> SovereigntyAsserter:
        """Add a layer with its ownership status."""
        self._inner.with_layer(layer, ownership)
        return self
    
    def assert_all_owned(self) -> bool:
        """Assert all layers are owned."""
        return self._inner.assert_all_owned()
    
    def assert_score_above(self, threshold: float) -> bool:
        """Assert sovereignty score is above threshold."""
        return self._inner.assert_score_above(threshold)
    
    @property
    def score(self) -> float:
        """Calculate sovereignty score."""
        return self._inner.calculate_score()
    
    @property
    def owned_count(self) -> int:
        """Get number of owned layers."""
        return self._inner.owned_count
    
    @property
    def total_count(self) -> int:
        """Get total number of layers."""
        return self._inner.total_count
    
    @property
    def verdict(self) -> str:
        """Get sovereignty verdict."""
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
