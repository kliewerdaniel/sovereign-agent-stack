"""Deterministic risk policy engine.

Risk policy lives OUTSIDE the LLM.
The LLM may recommend.
The policy engine decides.

Policy constraints are defined in knowledge artifacts and enforced here.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class RiskPolicy:
    """Deterministic risk policy constraints."""
    max_position_weight: float = 0.25
    max_gross_exposure: float = 1.0
    max_net_exposure: float = 0.80
    max_leverage: float = 1.5
    max_sector_exposure: float = 0.40
    max_turnover: float = 0.50
    max_daily_loss: float = 0.05       # 5% of portfolio
    max_drawdown: float = 0.20         # 20% portfolio drawdown
    max_order_value: float = 1_000_000
    min_liquidity: float = 1_000_000   # daily dollar volume
    approved_universe: list[str] = field(default_factory=list)
    max_single_name_concentration: float = 0.15
    min_positions: int = 3
    max_positions: int = 30

    def __post_init__(self):
        object.__setattr__(self, "_hash", self._compute_hash())

    @property
    def hash(self) -> str:
        return self._hash

    def _compute_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "max_position_weight": self.max_position_weight,
            "max_gross_exposure": self.max_gross_exposure,
            "max_net_exposure": self.max_net_exposure,
            "max_leverage": self.max_leverage,
            "max_sector_exposure": self.max_sector_exposure,
            "max_turnover": self.max_turnover,
            "max_daily_loss": self.max_daily_loss,
            "max_drawdown": self.max_drawdown,
            "max_order_value": self.max_order_value,
            "min_liquidity": self.min_liquidity,
            "approved_universe": self.approved_universe,
            "max_single_name_concentration": self.max_single_name_concentration,
            "min_positions": self.min_positions,
            "max_positions": self.max_positions,
        }


@dataclass
class RiskEvaluation:
    """Result of risk evaluation."""
    policy_version: str = ""
    policy_hash: str = ""
    gross_exposure: float = 0.0
    net_exposure: float = 0.0
    leverage: float = 0.0
    max_position_weight: float = 0.0
    turnover: float = 0.0
    daily_pnl: float = 0.0
    drawdown: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0
    breaches: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    is_compliant: bool = True
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(
                json.dumps(self.to_dict(), sort_keys=True, default=str).encode()
            ).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "content_hash"}


@dataclass
class TradeIntent:
    """Formal trade proposal with full provenance."""
    id: str = field(default_factory=lambda: str(hashlib.sha256(
        str(__import__('time').time()).encode()).hexdigest()[:16]))
    strategy_id: str = ""
    symbol: str = ""
    side: str = "buy"                # buy, sell, hold
    quantity: float = 0.0
    target_weight: float = 0.0
    price_assumption: float = 0.0
    reason: str = ""
    requested_by: str = "unknown"    # agent name
    risk_assessment: RiskEvaluation | None = None
    policy_evaluation: str = "pending"   # pending, approved, rejected
    authorization: str = "unauthorized"  # unauthorized, pending, authorized
    status: str = "proposed"         # proposed, validating, risk_review,
                                     # pending_approval, authorized,
                                     # executing, executed, rejected, cancelled
    timestamp: str = field(default_factory=lambda: __import__('datetime',
        fromlist=['datetime']).datetime.now(__import__('datetime',
        fromlist=['timezone'], level=0).timezone.utc).isoformat())
    provenance: dict = field(default_factory=dict)
    parent_trade_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id, "strategy_id": self.strategy_id,
            "symbol": self.symbol, "side": self.side,
            "quantity": self.quantity, "target_weight": self.target_weight,
            "price_assumption": self.price_assumption, "reason": self.reason,
            "requested_by": self.requested_by,
            "risk_assessment": self.risk_assessment.to_dict() if self.risk_assessment else None,
            "policy_evaluation": self.policy_evaluation,
            "authorization": self.authorization, "status": self.status,
            "timestamp": self.timestamp, "provenance": self.provenance,
            "parent_trade_id": self.parent_trade_id,
        }


class RiskEngine:
    """Deterministic risk evaluation engine."""

    def __init__(self, policy: RiskPolicy | None = None):
        self.policy = policy or RiskPolicy()
        self._version = "1.0.0"

    def evaluate(self, weights: dict[str, float],
                 positions: dict[str, float],
                 prices: dict[str, float],
                 returns: np.ndarray | None = None
                 ) -> RiskEvaluation:
        """Evaluate portfolio against risk policy.

        Returns RiskEvaluation with breaches list.
        """
        breaches = []
        warnings = []

        # Gross exposure
        gross = sum(abs(w) for w in weights.values())
        if gross > self.policy.max_gross_exposure:
            breaches.append({
                "type": "gross_exposure",
                "limit": self.policy.max_gross_exposure,
                "actual": gross,
                "severity": "high",
            })

        # Net exposure
        net = sum(weights.values())
        if abs(net) > self.policy.max_net_exposure:
            breaches.append({
                "type": "net_exposure",
                "limit": self.policy.max_net_exposure,
                "actual": net,
                "severity": "high",
            })

        # Max position weight
        for symbol, w in weights.items():
            if abs(w) > self.policy.max_position_weight:
                breaches.append({
                    "type": "position_weight",
                    "symbol": symbol,
                    "limit": self.policy.max_position_weight,
                    "actual": abs(w),
                    "severity": "medium",
                })

        # Leverage
        if gross > self.policy.max_leverage:
            breaches.append({
                "type": "leverage",
                "limit": self.policy.max_leverage,
                "actual": gross,
                "severity": "high",
            })

        # Approved universe
        if self.policy.approved_universe:
            for symbol in weights:
                if symbol not in self.policy.approved_universe:
                    breaches.append({
                        "type": "unapproved_universe",
                        "symbol": symbol,
                        "severity": "critical",
                    })

        # Liquidity check
        for symbol, pos in positions.items():
            if pos > 0 and prices.get(symbol, 0) * pos < self.policy.min_liquidity:
                warnings.append(f"Low liquidity: {symbol} position")

        is_compliant = len(breaches) == 0

        eval_result = RiskEvaluation(
            policy_version=self._version,
            policy_hash=self.policy.hash,
            gross_exposure=gross,
            net_exposure=net,
            leverage=gross,  # simplified
            max_position_weight=max((abs(w) for w in weights.values()), default=0),
            turnover=0.0,  # computed from trade history
            daily_pnl=0.0,  # computed from P&L
            drawdown=0.0,
            var_95=0.0,
            cvar_95=0.0,
            breaches=breaches,
            warnings=warnings,
            is_compliant=is_compliant,
        )
        return eval_result

    def evaluate_trade(self, trade: TradeIntent,
                       portfolio_weights: dict[str, float],
                       ) -> RiskEvaluation:
        """Evaluate a single trade intent against policy."""
        weights = dict(portfolio_weights)
        weights[trade.symbol] = weights.get(trade.symbol, 0) + trade.target_weight
        return self.evaluate(weights, {}, {})

    def authorize_trade(self, trade: TradeIntent,
                        portfolio_weights: dict[str, float]
                        ) -> TradeIntent:
        """Authorize or reject a trade based on risk policy."""
        evaluation = self.evaluate_trade(trade, portfolio_weights)
        trade.risk_assessment = evaluation

        if evaluation.is_compliant and not evaluation.breaches:
            trade.policy_evaluation = "approved"
            trade.authorization = "authorized"
            trade.status = "authorized"
        else:
            critical = [b for b in evaluation.breaches if b["severity"] == "critical"]
            if critical:
                trade.policy_evaluation = "rejected"
                trade.authorization = "rejected"
                trade.status = "rejected"
            else:
                trade.policy_evaluation = "approved_with_warnings"
                trade.authorization = "pending_approval"
                trade.status = "pending_approval"

        return trade

    def check_escalation(self, trade: TradeIntent) -> bool:
        """Check if trade requires human approval."""
        if trade.status == "rejected":
            return True
        return trade.authorization == "unauthorized"