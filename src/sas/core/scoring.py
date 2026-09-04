"""Sovereignty scoring engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from sas.core.config import (
    AuthBroker,
    LongTermProvider,
    MemoryProvider,
    Ownership,
    SASConfig,
    SubstrateType,
)


class LayerID(Enum):
    MODEL = "layer_1_model"
    HARNESS = "layer_2_harness"
    COMPUTE = "layer_3_compute"
    IDENTITY = "layer_4_identity"
    SHORT_TERM_MEMORY = "layer_5_short_term_memory"
    LONG_TERM_KNOWLEDGE = "layer_6_long_term_knowledge"
    AUTH = "layer_7_auth"
    PAYMENTS = "layer_8_payments"


@dataclass
class LayerScore:
    layer_id: LayerID
    name: str
    ownership: Ownership
    scored_as: Ownership  # may differ from ownership if manually overridden
    reasoning: str
    unavoidable_rental: bool = False


@dataclass
class SovereigntyReport:
    timestamp: datetime
    layers: list[LayerScore]
    owned_count: int
    total_count: int
    score: float  # 0.0 - 1.0
    previous_score: float | None = None
    drift: float | None = None  # score change since last report

    @property
    def verdict(self) -> str:
        if self.score >= 0.875:  # 7-8/8
            return "Fully Sovereign"
        elif self.score >= 0.625:  # 5-6/8
            return "Sovereign (target)"
        elif self.score >= 0.375:  # 3-4/8
            return "Partially sovereign"
        else:
            return "Rented"


def score_config(config: SASConfig) -> list[LayerScore]:
    """Score each layer based on SASConfig."""
    layers = []

    # Layer 1: Model
    # Owned if local model exists (even with API fallback)
    model_local = (
        config.model_primary is not None
        and config.model_primary.location == "local"
    )
    layers.append(LayerScore(
        layer_id=LayerID.MODEL,
        name="Model",
        ownership=Ownership.OWNED if model_local else Ownership.RENTED,
        scored_as=Ownership.OWNED if model_local else Ownership.RENTED,
        reasoning=(
            "Local model configured (sovereignty-irrelevant layer, but local is better)"
            if model_local
            else "API-only model (no local fallback)"
        ),
    ))

    # Layer 2: Harness
    # ARGO-based, self-hosted = owned
    layers.append(LayerScore(
        layer_id=LayerID.HARNESS,
        name="Harness",
        ownership=Ownership.OWNED,
        scored_as=Ownership.OWNED,
        reasoning="ARGO-based, self-hosted, MIT-licensed",
    ))

    # Layer 3: Compute
    compute_owned = config.substrate in (
        SubstrateType.LOCAL_DOCKER,
        SubstrateType.LOCAL_VM,
    )
    layers.append(LayerScore(
        layer_id=LayerID.COMPUTE,
        name="Compute Substrate",
        ownership=Ownership.OWNED if compute_owned else Ownership.RENTED,
        scored_as=Ownership.OWNED if compute_owned else Ownership.RENTED,
        reasoning=(
            f"Local substrate ({config.substrate.value})"
            if compute_owned
            else f"Cloud substrate ({config.substrate.value})"
        ),
    ))

    # Layer 4: Identity
    # Unavoidably rented
    layers.append(LayerScore(
        layer_id=LayerID.IDENTITY,
        name="Identity",
        ownership=Ownership.RENTED,
        scored_as=Ownership.RENTED,
        reasoning="Unavoidably rented (cannot self-host phone/MX records)",
        unavoidable_rental=True,
    ))

    # Layer 5: Short-term Memory
    short_term_owned = config.memory_short_term in (
        MemoryProvider.LOCAL_RAG,
        MemoryProvider.HONCHO_SELF_HOSTED,
    )
    layers.append(LayerScore(
        layer_id=LayerID.SHORT_TERM_MEMORY,
        name="Short-term Memory",
        ownership=Ownership.OWNED if short_term_owned else Ownership.RENTED,
        scored_as=Ownership.OWNED if short_term_owned else Ownership.RENTED,
        reasoning=(
            f"Local memory ({config.memory_short_term.value})"
            if short_term_owned
            else f"Cloud memory ({config.memory_short_term.value})"
        ),
    ))

    # Layer 6: Long-term Knowledge
    long_term_owned = config.memory_long_term == LongTermProvider.COMPILE_TIME_GRAPH
    layers.append(LayerScore(
        layer_id=LayerID.LONG_TERM_KNOWLEDGE,
        name="Long-term Knowledge",
        ownership=Ownership.OWNED if long_term_owned else Ownership.RENTED,
        scored_as=Ownership.OWNED if long_term_owned else Ownership.RENTED,
        reasoning=(
            "Compile-time knowledge graph (local markdown, versionable)"
            if long_term_owned
            else "Retrieval-only (no compile step, drift-prone)"
        ),
    ))

    # Layer 7: Auth
    auth_owned = config.auth_broker == AuthBroker.LOCAL_MCP_GATEWAY
    layers.append(LayerScore(
        layer_id=LayerID.AUTH,
        name="Auth",
        ownership=Ownership.OWNED if auth_owned else Ownership.RENTED,
        scored_as=Ownership.OWNED if auth_owned else Ownership.RENTED,
        reasoning=(
            "Local MCP gateway + encrypted vault"
            if auth_owned
            else "Hosted auth broker (Composio)"
        ),
    ))

    # Layer 8: Payments
    # Unavoidably transits third-party financial infrastructure
    layers.append(LayerScore(
        layer_id=LayerID.PAYMENTS,
        name="Payments",
        ownership=Ownership.RENTED,
        scored_as=Ownership.RENTED,
        reasoning="Unavoidably transits financial infrastructure",
        unavoidable_rental=True,
    ))

    # Apply manual overrides
    if config.overrides:
        for layer in layers:
            # Match by full enum value ("layer_5_short_term_memory") or short key ("layer_5")
            override = config.overrides.get(layer.layer_id.value)
            if override is None:
                # Extract layer number from enum value (e.g., "5" from "layer_5_short_term_memory")
                layer_num = layer.layer_id.value.split("_")[1] if "_" in layer.layer_id.value else None
                if layer_num:
                    for key, val in config.overrides.items():
                        # Match "layer_5" to layer_num "5"
                        if key == f"layer_{layer_num}":
                            override = val
                            break
            if override is not None:
                layer.scored_as = override
                layer.reasoning += " [MANUAL OVERRIDE]"

    return layers


def compute_score(layers: list[LayerScore]) -> tuple[int, int, float]:
    """Compute owned count, total count, and score."""
    # Exclude unavoidable rentals from the denominator
    scorable = [l for l in layers if not l.unavoidable_rental]
    owned = sum(1 for l in scorable if l.scored_as == Ownership.OWNED)
    total = len(scorable)
    score = owned / total if total > 0 else 0.0
    return owned, total, score


def generate_report(
    config: SASConfig,
    previous_score: float | None = None,
) -> SovereigntyReport:
    """Generate a full sovereignty report."""
    layers = score_config(config)
    owned, total, score = compute_score(layers)

    drift = None
    if previous_score is not None:
        drift = score - previous_score

    return SovereigntyReport(
        timestamp=datetime.utcnow(),
        layers=layers,
        owned_count=owned,
        total_count=total,
        score=score,
        previous_score=previous_score,
        drift=drift,
    )
