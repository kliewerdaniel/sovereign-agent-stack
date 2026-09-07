"""Research gates — risk and statistical gates for strategy evaluation.

A strategy must pass BOTH gates to be considered a candidate:

1. Risk gate: The strategy must satisfy the risk policy (position limits,
   drawdown limits, concentration limits, etc.)

2. Statistical gate: The strategy must have a positive Deflated Sharpe Ratio
   (DSR) and a PBO below a threshold (indicating the selection is not
   overfitted).

The gates are deterministic functions over immutable artifacts. They do
not depend on the model's opinion of the strategy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from sas.quant.provenance.artifacts import TrialArtifact
from sas.quant.risk import RiskEngine, RiskEvaluation, RiskPolicy, TradeIntent


@dataclass(frozen=True)
class GateResult:
    """Result of a gate evaluation."""

    passed: bool
    gate_name: str
    reason: str
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "gate_name": self.gate_name,
            "reason": self.reason,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class ResearchGateConfig:
    """Configuration for the research gates."""

    max_drawdown_limit: float = 0.20
    max_single_name_concentration: float = 0.25
    max_leverage: float = 1.5
    max_daily_loss: float = 0.05
    min_dsr: float = 0.0  # DSR must be > 0 (positive after deflation)
    max_pbo: float = 0.5  # PBO must be below this threshold
    require_positive_sharpe: bool = True

    def to_dict(self) -> dict:
        return {
            "max_drawdown_limit": self.max_drawdown_limit,
            "max_single_name_concentration": self.max_single_name_concentration,
            "max_leverage": self.max_leverage,
            "max_daily_loss": self.max_daily_loss,
            "min_dsr": self.min_dsr,
            "max_pbo": self.max_pbo,
            "require_positive_sharpe": self.require_positive_sharpe,
        }


class RiskGate:
    """Deterministic risk gate — LLM cannot bypass."""

    def __init__(self, risk_engine: RiskEngine | None = None, config: ResearchGateConfig | None = None):
        self.risk_engine = risk_engine or RiskEngine()
        self.config = config or ResearchGateConfig()

    def evaluate(self, trial: TrialArtifact, trade: TradeIntent | None = None) -> GateResult:
        """Evaluate a trial against the risk policy."""
        details = {}

        # Check drawdown
        if trial.backtest_result:
            max_dd = trial.backtest_result.get("max_drawdown", 0.0)
            details["max_drawdown"] = max_dd
            if abs(max_dd) > self.config.max_drawdown_limit:
                return GateResult(
                    passed=False,
                    gate_name="risk_gate",
                    reason=f"Max drawdown {abs(max_dd):.2%} exceeds limit {self.config.max_drawdown_limit:.2%}",
                    details=details,
                )

            # Check Sharpe
            sharpe = trial.backtest_result.get("sharpe_ratio", 0.0)
            details["sharpe_ratio"] = sharpe
            if self.config.require_positive_sharpe and sharpe <= 0:
                return GateResult(
                    passed=False,
                    gate_name="risk_gate",
                    reason=f"Sharpe ratio {sharpe:.4f} is not positive",
                    details=details,
                )

        # Check concentration if trade provided
        if trade:
            # Simplified concentration check
            target_weight = trade.target_weight
            details["target_weight"] = target_weight
            if target_weight > self.config.max_single_name_concentration:
                return GateResult(
                    passed=False,
                    gate_name="risk_gate",
                    reason=f"Target weight {target_weight:.2%} exceeds concentration limit {self.config.max_single_name_concentration:.2%}",
                    details=details,
                )

        return GateResult(
            passed=True,
            gate_name="risk_gate",
            reason="Strategy passes risk policy",
            details=details,
        )


class StatisticalGate:
    """Statistical gate — DSR and PBO must indicate non-overfitted selection."""

    def __init__(self, config: ResearchGateConfig | None = None):
        self.config = config or ResearchGateConfig()

    def evaluate(
        self,
        trial: TrialArtifact,
        dsr_value: float | None = None,
        pbo_value: float | None = None,
    ) -> GateResult:
        """Evaluate a trial against statistical criteria."""
        details = {}

        # Check DSR
        if dsr_value is not None:
            details["dsr"] = dsr_value
            if dsr_value <= self.config.min_dsr:
                return GateResult(
                    passed=False,
                    gate_name="statistical_gate",
                    reason=f"DSR {dsr_value:.4f} is not positive (minimum: {self.config.min_dsr})",
                    details=details,
                )

        # Check PBO
        if pbo_value is not None:
            details["pbo"] = pbo_value
            if pbo_value > self.config.max_pbo:
                return GateResult(
                    passed=False,
                    gate_name="statistical_gate",
                    reason=f"PBO {pbo_value:.4f} exceeds threshold {self.config.max_pbo}",
                    details=details,
                )

        return GateResult(
            passed=True,
            gate_name="statistical_gate",
            reason="Strategy passes statistical criteria",
            details=details,
        )


class ResearchGates:
    """Combined research gates — risk + statistical."""

    def __init__(
        self,
        config: ResearchGateConfig | None = None,
        risk_gate: RiskGate | None = None,
        statistical_gate: StatisticalGate | None = None,
    ):
        self.config = config or ResearchGateConfig()
        self.risk_gate = risk_gate or RiskGate(config=self.config)
        self.statistical_gate = statistical_gate or StatisticalGate(config=self.config)

    def evaluate(
        self,
        trial: TrialArtifact,
        trade: TradeIntent | None = None,
        dsr_value: float | None = None,
        pbo_value: float | None = None,
    ) -> tuple[GateResult, GateResult]:
        """Evaluate a trial against both gates."""
        risk_result = self.risk_gate.evaluate(trial, trade)
        stat_result = self.statistical_gate.evaluate(trial, dsr_value, pbo_value)
        return risk_result, stat_result

    def to_dict(self) -> dict:
        return {
            "risk_gate": self.risk_gate.config.to_dict(),
            "statistical_gate": self.statistical_gate.config.to_dict(),
        }
