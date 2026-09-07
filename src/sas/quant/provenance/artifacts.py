"""Typed artifact definitions for governed research experiments.

These are the first-class artifacts that the experiment produces:
- TrialArtifact: a single strategy proposal + its evaluation
- CritiqueArtifact: the model's self-critique of a trial
- BaselineArtifact: the mandatory buy-and-hold baseline
- HoldoutArtifact: the one-shot holdout evaluation
- ResearchDecision: the final decision with full provenance

All artifacts are immutable once created. They form the statistical
substrate that the statistics layer operates on.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional


@dataclass(frozen=True)
class TrialArtifact:
    """A single strategy proposal and its complete evaluation.

    Every strategy proposal becomes a first-class trial artifact.
    A strategy that is proposed but never backtested is distinguishable
    from one that was actually evaluated.

    The trial boundary is an execution boundary: a revision creates
    a completely new trial with a new provenance identity.
    """

    trial_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    experiment_id: str = ""
    parent_trial_id: str | None = None  # for revisions
    trial_number: int = 0
    strategy_spec: dict = field(default_factory=dict)
    model_id: str = ""
    task_id: str = ""
    data_window: tuple[str, str] = ("", "")
    random_seed: int = 42
    parameterization: dict = field(default_factory=dict)
    backtest_result: dict | None = None
    return_series: list[float] = field(default_factory=list)
    rejection_reason: str | None = None
    is_incumbent: bool = False
    critique_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    provenance_event_ids: list[str] = field(default_factory=list)

    @property
    def sharpe_ratio(self) -> float | None:
        if self.backtest_result and "sharpe_ratio" in self.backtest_result:
            return self.backtest_result["sharpe_ratio"]
        return None

    @property
    def total_return(self) -> float | None:
        if self.backtest_result and "total_return" in self.backtest_result:
            return self.backtest_result["total_return"]
        return None

    @property
    def max_drawdown(self) -> float | None:
        if self.backtest_result and "max_drawdown" in self.backtest_result:
            return self.backtest_result["max_drawdown"]
        return None

    @property
    def was_evaluated(self) -> bool:
        return self.backtest_result is not None

    def to_dict(self) -> dict:
        return {
            "trial_id": self.trial_id,
            "experiment_id": self.experiment_id,
            "parent_trial_id": self.parent_trial_id,
            "trial_number": self.trial_number,
            "strategy_spec": dict(self.strategy_spec),
            "model_id": self.model_id,
            "task_id": self.task_id,
            "data_window": list(self.data_window),
            "random_seed": self.random_seed,
            "parameterization": dict(self.parameterization),
            "backtest_result": dict(self.backtest_result) if self.backtest_result else None,
            "return_series": list(self.return_series),
            "rejection_reason": self.rejection_reason,
            "is_incumbent": self.is_incumbent,
            "critique_id": self.critique_id,
            "created_at": self.created_at,
            "provenance_event_ids": list(self.provenance_event_ids),
        }


@dataclass(frozen=True)
class CritiqueArtifact:
    """Structured self-critique of a trial.

    The model produces this after backtest. It identifies weaknesses
    and either terminates the trial or produces a revised strategy.
    A revision creates a new trial with parent_trial_id pointing here.

    Machine-evaluable fields are authoritative. The model's original
    textual reasoning is preserved as an optional field.
    """

    critique_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    trial_id: str = ""
    experiment_id: str = ""
    weaknesses: list[dict] = field(default_factory=list)  # [{name, severity, evidence}]
    severity: str = "low"  # low | medium | high
    evidence: list[str] = field(default_factory=list)
    recommendation: str = ""  # "terminate" | "revise" | "accept"
    action: str = ""  # what the model decided to do
    parent_trial_id: str | None = None
    revised_trial_id: str | None = None  # set if action == "revise"
    reasoning: str = ""  # model's original textual reasoning
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        return {
            "critique_id": self.critique_id,
            "trial_id": self.trial_id,
            "experiment_id": self.experiment_id,
            "weaknesses": list(self.weaknesses),
            "severity": self.severity,
            "evidence": list(self.evidence),
            "recommendation": self.recommendation,
            "action": self.action,
            "parent_trial_id": self.parent_trial_id,
            "revised_trial_id": self.revised_trial_id,
            "reasoning": self.reasoning[:2000],
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class BaselineArtifact:
    """Mandatory buy-and-hold baseline for a QuantWorld.

    Every experiment must produce a baseline. The baseline is defined
    by the world or experiment configuration — it is not hardcoded.

    For an equity universe, this is typically an equally weighted
    buy-and-hold of the available universe. The abstraction supports
    a designated benchmark (e.g. SPY) when the world explicitly defines one.

    The baseline uses the same permitted temporal boundaries and
    transaction cost assumptions as the strategy where applicable.
    """

    baseline_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    experiment_id: str = ""
    baseline_type: str = "buy_and_hold"  # buy_and_hold | designated_benchmark
    benchmark_symbol: str | None = None  # e.g. "SPY" if designated
    universe: list[str] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)
    data_window: tuple[str, str] = ("", "")
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    volatility: float = 0.0
    return_series: list[float] = field(default_factory=list)
    transaction_costs: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        return {
            "baseline_id": self.baseline_id,
            "experiment_id": self.experiment_id,
            "baseline_type": self.baseline_type,
            "benchmark_symbol": self.benchmark_symbol,
            "universe": list(self.universe),
            "weights": dict(self.weights),
            "data_window": list(self.data_window),
            "total_return": self.total_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "volatility": self.volatility,
            "return_series": list(self.return_series),
            "transaction_costs": self.transaction_costs,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BaselineArtifact":
        """Reconstruct from a dictionary."""
        return cls(
            baseline_id=data.get("baseline_id", ""),
            experiment_id=data.get("experiment_id", ""),
            baseline_type=data.get("baseline_type", "buy_and_hold"),
            benchmark_symbol=data.get("benchmark_symbol"),
            universe=list(data.get("universe", [])),
            weights=dict(data.get("weights", {})),
            data_window=tuple(data.get("data_window", ["", ""])),
            total_return=data.get("total_return", 0.0),
            sharpe_ratio=data.get("sharpe_ratio", 0.0),
            max_drawdown=data.get("max_drawdown", 0.0),
            volatility=data.get("volatility", 0.0),
            return_series=list(data.get("return_series", [])),
            transaction_costs=data.get("transaction_costs", 0.0),
            created_at=data.get("created_at", ""),
        )


@dataclass(frozen=True)
class HoldoutArtifact:
    """One-shot holdout evaluation.

    The holdout is evaluated exactly once, after the research phase
    terminates. The strategy evaluated on holdout is immutable —
    the model receives no feedback from the holdout.

    This artifact records the holdout performance and whether the
    strategy's holdout performance is consistent with its in-sample
    performance.
    """

    holdout_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    experiment_id: str = ""
    trial_id: str = ""  # the incumbent trial being evaluated
    holdout_window: tuple[str, str] = ("", "")
    strategy_total_return: float = 0.0
    strategy_sharpe_ratio: float = 0.0
    strategy_max_drawdown: float = 0.0
    baseline_total_return: float = 0.0
    baseline_sharpe_ratio: float = 0.0
    outperformed_baseline: bool = False
    is_consistent: bool = True  # holdout consistent with in-sample?
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        return {
            "holdout_id": self.holdout_id,
            "experiment_id": self.experiment_id,
            "trial_id": self.trial_id,
            "holdout_window": list(self.holdout_window),
            "strategy_total_return": self.strategy_total_return,
            "strategy_sharpe_ratio": self.strategy_sharpe_ratio,
            "strategy_max_drawdown": self.strategy_max_drawdown,
            "baseline_total_return": self.baseline_total_return,
            "baseline_sharpe_ratio": self.baseline_sharpe_ratio,
            "outperformed_baseline": self.outperformed_baseline,
            "is_consistent": self.is_consistent,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HoldoutArtifact":
        """Reconstruct from a dictionary."""
        return cls(
            holdout_id=data.get("holdout_id", ""),
            experiment_id=data.get("experiment_id", ""),
            trial_id=data.get("trial_id", ""),
            holdout_window=tuple(data.get("holdout_window", ["", ""])),
            strategy_total_return=data.get("strategy_total_return", 0.0),
            strategy_sharpe_ratio=data.get("strategy_sharpe_ratio", 0.0),
            strategy_max_drawdown=data.get("strategy_max_drawdown", 0.0),
            baseline_total_return=data.get("baseline_total_return", 0.0),
            baseline_sharpe_ratio=data.get("baseline_sharpe_ratio", 0.0),
            outperformed_baseline=data.get("outperformed_baseline", False),
            is_consistent=data.get("is_consistent", True),
            notes=data.get("notes", ""),
            created_at=data.get("created_at", ""),
        )


@dataclass(frozen=True)
class ResearchDecision:
    """The final research decision with full provenance.

    The final research decision must be derivable entirely from the
    immutable experiment artifacts and event history. The model cannot
    alter a previous trial — it can only create another artifact that
    references the previous one.

    Three outcomes:
    - no_strategy_passed: the search failed to produce an admissible strategy
    - passed_but_no_value: passed gates but didn't beat baseline
    - candidate: passed gates and beat baseline
    """

    decision_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    experiment_id: str = ""
    outcome: str = "no_strategy_passed"  # no_strategy_passed | passed_but_no_value | candidate
    incumbent_trial_id: str | None = None
    baseline_id: str = ""
    holdout_id: str = ""
    statistical_evaluation_id: str = ""
    rationale: str = ""
    trial_count: int = 0
    evaluated_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "experiment_id": self.experiment_id,
            "outcome": self.outcome,
            "incumbent_trial_id": self.incumbent_trial_id,
            "baseline_id": self.baseline_id,
            "holdout_id": self.holdout_id,
            "statistical_evaluation_id": self.statistical_evaluation_id,
            "rationale": self.rationale,
            "trial_count": self.trial_count,
            "evaluated_count": self.evaluated_count,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchDecision":
        """Reconstruct from a dictionary."""
        return cls(
            decision_id=data.get("decision_id", ""),
            experiment_id=data.get("experiment_id", ""),
            outcome=data.get("outcome", "no_strategy_passed"),
            incumbent_trial_id=data.get("incumbent_trial_id"),
            baseline_id=data.get("baseline_id", ""),
            holdout_id=data.get("holdout_id", ""),
            statistical_evaluation_id=data.get("statistical_evaluation_id", ""),
            rationale=data.get("rationale", ""),
            trial_count=data.get("trial_count", 0),
            evaluated_count=data.get("evaluated_count", 0),
            created_at=data.get("created_at", ""),
        )
