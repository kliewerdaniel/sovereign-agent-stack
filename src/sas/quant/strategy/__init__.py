"""Strategy artifact definition — a structured, reproducible strategy object.

A strategy is a first-class artifact that can be:
- Versioned
- Reproduced (same data + params + engine → same backtest)
- Traced through provenance
- Validated against policy
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class SignalDefinition:
    """What constitutes a trading signal."""
    name: str
    type: str                    # "momentum", "mean_reversion", "factor", "ml"
    parameters: dict = field(default_factory=dict)
    lookback_periods: int = 20


@dataclass(frozen=True)
class PositionSizing:
    """How positions are sized."""
    method: str = "fixed_weight"   # fixed_weight, volatility_target, kelly
    target_weight: float = 0.10
    max_position: float = 0.25
    min_position: float = 0.01


@dataclass(frozen=True)
class TransactionCosts:
    """Cost assumptions for backtesting."""
    commission_per_share: float = 0.005
    commission_per_trade: float = 0.0
    slippage_bps: float = 5.0      # basis points
    market_impact_bps: float = 2.0
    spread_bps: float = 3.0

    def total_cost_per_share(self, price: float, shares: float) -> float:
        """Total transaction cost per share."""
        commission = self.commission_per_share * shares
        slip = price * (self.slippage_bps / 10000) * shares
        impact = price * (self.market_impact_bps / 10000) * shares
        spread = price * (self.spread_bps / 10000) * shares
        return commission + slip + impact + spread


@dataclass(frozen=True)
class RiskConstraints:
    """Strategy-level risk constraints."""
    max_position_weight: float = 0.25
    max_gross_exposure: float = 1.0
    max_leverage: float = 1.5
    max_sector_exposure: float = 0.40
    max_turnover: float = 0.50
    max_order_value: float = 1_000_000
    min_liquidity: float = 1_000_000  # daily dollar volume
    max_drawdown_limit: float = 0.20


@dataclass(frozen=True)
class StrategyArtifact:
    """A complete, versioned strategy artifact.

    If the same dataset, parameters, engine version, and seed are supplied,
    the backtest should produce the same result (deterministic reproducibility).
    """
    strategy_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    version: str = "1.0.0"
    name: str = ""
    universe: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    signal_definition: SignalDefinition | None = None
    entry_rules: dict = field(default_factory=dict)
    exit_rules: dict = field(default_factory=dict)
    position_sizing: PositionSizing = field(default_factory=PositionSizing)
    rebalance_frequency: str = "monthly"  # daily, weekly, monthly, quarterly
    transaction_costs: TransactionCosts = field(default_factory=TransactionCosts)
    risk_constraints: RiskConstraints = field(default_factory=RiskConstraints)
    training_period: tuple[str, str] = ("", "")
    validation_period: tuple[str, str] = ("", "")
    test_period: tuple[str, str] = ("", "")
    engine_version: str = "1.0.0"
    dataset_version: str = ""
    created_by: str = "unknown"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    assumptions: dict = field(default_factory=dict)
    parent_strategy_id: Optional[str] = None

    def __post_init__(self):
        # Compute content hash for reproducibility verification
        object.__setattr__(self, "_content_hash", self._compute_hash())

    def _compute_hash(self) -> str:
        """Deterministic hash of strategy parameters."""
        d = self.to_dict(exclude=["strategy_id", "created_at"])
        return hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:16]

    @property
    def content_hash(self) -> str:
        return self._content_hash

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        exclude = exclude or []
        d = {
            "strategy_id": self.strategy_id,
            "version": self.version,
            "name": self.name,
            "universe": self.universe,
            "features": self.features,
            "signal_definition": self.signal_definition.__dict__ if self.signal_definition else None,
            "entry_rules": self.entry_rules,
            "exit_rules": self.exit_rules,
            "position_sizing": self.position_sizing.__dict__,
            "rebalance_frequency": self.rebalance_frequency,
            "transaction_costs": self.transaction_costs.__dict__,
            "risk_constraints": self.risk_constraints.__dict__,
            "training_period": self.training_period,
            "validation_period": self.validation_period,
            "test_period": self.test_period,
            "engine_version": self.engine_version,
            "dataset_version": self.dataset_version,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "assumptions": self.assumptions,
            "parent_strategy_id": self.parent_strategy_id,
        }
        for key in exclude:
            d.pop(key, None)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> StrategyArtifact:
        # Reconstruct nested dataclasses
        sd = d.get("signal_definition")
        signal = SignalDefinition(**sd) if sd else None
        ps = PositionSizing(**d.get("position_sizing", {}))
        tc = TransactionCosts(**d.get("transaction_costs", {}))
        rc = RiskConstraints(**d.get("risk_constraints", {}))
        return cls(
            strategy_id=d.get("strategy_id", str(uuid.uuid4())[:12]),
            version=d.get("version", "1.0.0"),
            name=d.get("name", ""),
            universe=d.get("universe", []),
            features=d.get("features", []),
            signal_definition=signal,
            entry_rules=d.get("entry_rules", {}),
            exit_rules=d.get("exit_rules", {}),
            position_sizing=ps,
            rebalance_frequency=d.get("rebalance_frequency", "monthly"),
            transaction_costs=tc,
            risk_constraints=rc,
            training_period=d.get("training_period", ("", "")),
            validation_period=d.get("validation_period", ("", "")),
            test_period=d.get("test_period", ("", "")),
            engine_version=d.get("engine_version", "1.0.0"),
            dataset_version=d.get("dataset_version", ""),
            created_by=d.get("created_by", "unknown"),
            created_at=d.get("created_at", ""),
            assumptions=d.get("assumptions", {}),
            parent_strategy_id=d.get("parent_strategy_id"),
        )