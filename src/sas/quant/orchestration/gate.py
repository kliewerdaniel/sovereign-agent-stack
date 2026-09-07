"""Trade authorization gate.

The gate is a DETERMINISTIC component. The LLM cannot bypass it.
No order reaches the broker without passing through here.

The gate enforces:
1. Risk policy compliance (via RiskEngine)
2. Session-level limits (max trades per session, max single-order value)
3. Human-in-the-loop approval (blocks on stdin by default)

The gate sets ``TradeIntent.status`` to one of:
    authorized | rejected | pending_approval

Only ``authorized`` trades may be submitted to the broker.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Optional

from sas.quant.broker import Order, OrderStatus
from sas.quant.risk import RiskEngine, RiskPolicy, TradeIntent


@dataclass
class SessionLimits:
    """Session-level trading limits."""
    max_trades_per_session: int = 10
    max_order_value_usd: float = 10_000.0
    auto_approve: bool = False  # If True, skip human approval (for CI/tests)


@dataclass
class AuthorizationResult:
    """Result of the authorization gate."""
    trade: TradeIntent
    approved: bool
    reason: str
    risk_breaches: list[dict] = field(default_factory=list)
    session_breaches: list[str] = field(default_factory=list)


class TradeAuthorization:
    """Deterministic trade authorization gate.

    The LLM proposes trades. The gate decides if they're allowed.
    """

    def __init__(
        self,
        risk_engine: RiskEngine | None = None,
        session_limits: SessionLimits | None = None,
    ):
        self.risk_engine = risk_engine or RiskEngine()
        self.session_limits = session_limits or SessionLimits()
        self._trades_this_session: int = 0

    def authorize(
        self,
        trade: TradeIntent,
        portfolio_weights: dict[str, float],
    ) -> AuthorizationResult:
        """Evaluate a trade intent through the authorization gate.

        Args:
            trade: The proposed trade intent.
            portfolio_weights: Current portfolio weights for risk evaluation.

        Returns:
            ``AuthorizationResult`` with approval decision and reason.
        """
        # 1. Check session limits
        session_breaches = self._check_session_limits(trade)
        if session_breaches:
            trade.status = "rejected"
            trade.authorization = "rejected"
            trade.policy_evaluation = "rejected"
            return AuthorizationResult(
                trade=trade,
                approved=False,
                reason=f"Session limit exceeded: {'; '.join(session_breaches)}",
                session_breaches=session_breaches,
            )

        # 2. Risk evaluation
        evaluation = self.risk_engine.evaluate_trade(trade, portfolio_weights)
        trade.risk_assessment = evaluation

        if not evaluation.is_compliant:
            critical = [b for b in evaluation.breaches if b["severity"] == "critical"]
            if critical:
                trade.status = "rejected"
                trade.authorization = "rejected"
                trade.policy_evaluation = "rejected"
                return AuthorizationResult(
                    trade=trade,
                    approved=False,
                    reason=f"Critical risk breach: {critical[0]['type']}",
                    risk_breaches=evaluation.breaches,
                )
            # Non-critical breaches — escalate to human
            trade.status = "pending_approval"
            trade.authorization = "pending_approval"
            trade.policy_evaluation = "approved_with_warnings"
        else:
            trade.status = "authorized"
            trade.authorization = "authorized"
            trade.policy_evaluation = "approved"

        # 3. Human-in-the-loop approval
        if self.session_limits.auto_approve:
            # Auto-approve for CI/tests
            trade.status = "authorized"
            trade.authorization = "authorized"
            return AuthorizationResult(
                trade=trade,
                approved=True,
                reason="Auto-approved (auto_approve=True)",
            )

        # Block on stdin for human approval
        approved = self._prompt_approval(trade, evaluation)
        if approved:
            trade.status = "authorized"
            trade.authorization = "authorized"
            return AuthorizationResult(
                trade=trade,
                approved=True,
                reason="Human approved",
            )
        else:
            trade.status = "rejected"
            trade.authorization = "rejected"
            return AuthorizationResult(
                trade=trade,
                approved=False,
                reason="Human rejected",
            )

    def _check_session_limits(self, trade: TradeIntent) -> list[str]:
        """Check session-level limits. Returns list of breach descriptions."""
        breaches = []
        if self._trades_this_session >= self.session_limits.max_trades_per_session:
            breaches.append(
                f"Max trades per session ({self.session_limits.max_trades_per_session}) reached"
            )
        order_value = trade.quantity * trade.price_assumption
        if order_value > self.session_limits.max_order_value_usd:
            breaches.append(
                f"Order value ${order_value:,.0f} exceeds max ${self.session_limits.max_order_value_usd:,.0f}"
            )
        return breaches

    def _prompt_approval(self, trade: TradeIntent, evaluation) -> bool:
        """Prompt the user for approval via stdin.

        Returns True if approved, False if rejected.
        """
        print("\n" + "=" * 60)
        print("  TRADE APPROVAL REQUIRED")
        print("=" * 60)
        print(f"  Symbol:      {trade.symbol}")
        print(f"  Side:        {trade.side}")
        print(f"  Quantity:    {trade.quantity}")
        print(f"  Price:       ${trade.price_assumption:,.2f}")
        print(f"  Value:       ${trade.quantity * trade.price_assumption:,.2f}")
        print(f"  Reason:      {trade.reason}")
        print(f"  Risk:        {'COMPLIANT' if evaluation.is_compliant else 'BREACHES'}")
        if evaluation.breaches:
            for b in evaluation.breaches:
                print(f"    - {b['type']} ({b['severity']})")
        print("=" * 60)

        while True:
            try:
                response = input("  Approve this trade? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return False
            if response in ("y", "yes"):
                return True
            if response in ("n", "no", ""):
                return False
            print("  Please enter 'y' or 'n'.")

    def record_trade(self) -> None:
        """Record that a trade was executed (for session limit tracking)."""
        self._trades_this_session += 1

    @property
    def trades_remaining(self) -> int:
        """Number of trades remaining in this session."""
        return max(0, self.session_limits.max_trades_per_session - self._trades_this_session)
