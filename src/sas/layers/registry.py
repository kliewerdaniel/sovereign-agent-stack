# ── Layer Registry — single source of truth for the 8 sovereignty layers ──────

from __future__ import annotations

from sas.core.config import SASConfig
from sas.core.scoring import (
    LayerID,
    Ownership,
    compute_score,
    score_config,
)


class LayerRegistry:
    """Single source of truth for the 8 sovereignty layers.

    Every layer ID, name, and Protocol class lives here. The sovereignty
    scorer (``sas.core.scoring.score_config``) is the one place that
    consumes the registry's layer list to compute ownership — so the
    layer definitions and the scoring logic cannot drift apart.
    """

    _LAYER_IDS = [
        LayerID.MODEL,
        LayerID.HARNESS,
        LayerID.COMPUTE,
        LayerID.IDENTITY,
        LayerID.SHORT_TERM_MEMORY,
        LayerID.LONG_TERM_KNOWLEDGE,
        LayerID.AUTH,
        LayerID.PAYMENTS,
    ]

    def __init__(self, config: SASConfig | None = None) -> None:
        self._config = config

    def list_layers(self, scored: bool = False) -> list[LayerID]:
        """Return all 8 layer IDs. If ``scored``, return only scorable layers
        (excludes the two unavoidable-rental layers: identity, payments)."""
        if not scored:
            return list(self._LAYER_IDS)
        return [lid for lid in self._LAYER_IDS
                if not self._is_unavoidable_rental(lid)]

    def get_layer(self, layer_id: LayerID | str) -> LayerID:
        """Normalize a layer reference to a ``LayerID`` enum.

        Accepts: the enum itself, the full enum value (``"layer_1_model"``),
        or the short numeric key (``"1"`` or ``"layer_1"``).
        """
        if isinstance(layer_id, LayerID):
            return layer_id
        s = str(layer_id)
        # Full value match first
        for lid in self._LAYER_IDS:
            if lid.value == s:
                return lid
        # Short numeric suffix: "1" or "layer_1" -> layer_1_model
        suffix = s.replace("layer_", "")
        if suffix.isdigit():
            for lid in self._LAYER_IDS:
                if lid.value.split("_")[1] == suffix:
                    return lid
        raise KeyError(f"Unknown layer: {layer_id}")

    def is_owned(self, layer_id: LayerID | str, config: SASConfig | None = None) -> bool:
        """Return True if the layer scores as owned under the given config."""
        lid = self.get_layer(layer_id)
        cfg = config or self._config
        if cfg is None:
            return False
        layers = score_config(cfg)
        for l in layers:
            if l.layer_id == lid:
                return l.scored_as == Ownership.OWNED
        return False

    def is_unavoidable_rental(self, layer_id: LayerID | str) -> bool:
        """Return True if the layer is structurally rented (identity, payments)."""
        lid = self.get_layer(layer_id)
        return self._is_unavoidable_rental(lid)

    @staticmethod
    def _is_unavoidable_rental(layer_id: LayerID) -> bool:
        return layer_id in (LayerID.IDENTITY, LayerID.PAYMENTS)

    def sovereignty_score(self, config: SASConfig | None = None) -> tuple[int, int, float]:
        """Compute (owned, scorable_total, score) for the given config."""
        cfg = config or self._config
        if cfg is None:
            return 0, 0, 0.0
        layers = score_config(cfg)
        owned, total, score = compute_score(layers)
        return owned, total, score

    @property
    def config(self) -> SASConfig | None:
        return self._config

    @config.setter
    def config(self, value: SASConfig) -> None:
        self._config = value
