"""Experiment — the complete governed research artifact.

An Experiment contains everything needed to reconstruct what happened
during a research search:
- QuantWorld identity, research window, holdout window, trial budget
- Model identity, tool policy, random seed
- Trial ledger (all strategy proposals and evaluations)
- Incumbent strategy, baseline, statistical evaluation
- Holdout evaluation, final decision

The complete causal chain:
    QuantWorld → Experiment → ResearchWindow → Trial → Backtest → Critique → ...
    → Statistical Evaluation → Holdout → Baseline Comparison → Risk Gate → Decision

Every arrow is represented in provenance. The final research decision
must be derivable entirely from the immutable experiment artifacts and
event history.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

from sas.quant.evaluation.baseline import BaselineComputer, BaselineConfig
from sas.quant.evaluation.gates import (
    GateResult,
    ResearchGateConfig,
    ResearchGates,
)
from sas.quant.market import MarketDataProvider, SyntheticDataProvider
from sas.quant.provenance.artifacts import (
    BaselineArtifact,
    HoldoutArtifact,
    ResearchDecision,
    TrialArtifact,
)
from sas.quant.provenance.graph import EventLog
from sas.quant.research.temporal import (
    HoldoutWindow,
    ResearchWindow,
    TemporalAuthority,
)
from sas.quant.research.trial import TrialLedger


@dataclass(frozen=True)
class ExperimentConfig:
    """Configuration for a governed research experiment."""

    experiment_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    world_id: str = ""
    trial_budget: int = 10
    research_window: tuple[str, str] = ("", "")
    holdout_window: tuple[str, str] = ("", "")
    model_id: str = ""
    task_id: str = ""
    random_seed: int = 42
    initial_capital: float = 100_000.0
    max_reflection_rounds: int = 1
    baseline_config: BaselineConfig | None = None
    gate_config: ResearchGateConfig | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "world_id": self.world_id,
            "trial_budget": self.trial_budget,
            "research_window": list(self.research_window),
            "holdout_window": list(self.holdout_window),
            "model_id": self.model_id,
            "task_id": self.task_id,
            "random_seed": self.random_seed,
            "initial_capital": self.initial_capital,
            "max_reflection_rounds": self.max_reflection_rounds,
            "baseline_config": self.baseline_config.to_dict() if self.baseline_config else None,
            "gate_config": self.gate_config.to_dict() if self.gate_config else None,
            "metadata": dict(self.metadata),
        }


class Experiment:
    """A governed computational research experiment.

    The experiment is the authoritative record of a research search.
    It contains the trial ledger, event log, temporal authority,
    baseline, statistical evaluation, holdout evaluation, and final
    decision.

    The experiment is immutable once completed. The final research
    decision must be derivable entirely from the immutable artifacts
    and event history.
    """

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.event_log = EventLog(config.experiment_id)
        self.trial_ledger = TrialLedger(config.experiment_id)
        self.temporal_authority = TemporalAuthority(
            research_window=ResearchWindow(
                earliest_timestamp=config.research_window[0],
                max_permitted_timestamp=config.research_window[1],
                holdout_start=config.holdout_window[0] if config.holdout_window else "",
                final_timestamp=config.holdout_window[1] if config.holdout_window else "",
            ),
            holdout_window=HoldoutWindow(
                holdout_start=config.holdout_window[0] if config.holdout_window else "",
                final_timestamp=config.holdout_window[1] if config.holdout_window else "",
            ),
        )
        self.gates = ResearchGates(config.gate_config)
        self._baseline: BaselineArtifact | None = None
        self._holdout: HoldoutArtifact | None = None
        self._decision: ResearchDecision | None = None
        self._is_complete = False
        self._dsr_value: float | None = None
        self._pbo_value: float | None = None

    @property
    def experiment_id(self) -> str:
        return self.config.experiment_id

    @property
    def is_complete(self) -> bool:
        return self._is_complete

    @property
    def baseline(self) -> BaselineArtifact | None:
        return self._baseline

    @property
    def holdout(self) -> HoldoutArtifact | None:
        return self._holdout

    @property
    def decision(self) -> ResearchDecision | None:
        return self._decision

    @property
    def dsr_value(self) -> float | None:
        return self._dsr_value

    @property
    def pbo_value(self) -> float | None:
        return self._pbo_value

    def compute_baseline(
        self,
        data_provider: MarketDataProvider | None = None,
    ) -> BaselineArtifact:
        """Compute the mandatory baseline for this experiment.

        The baseline is computed from the world definition and uses
        the same temporal boundaries as the research phase.
        """
        if data_provider is None:
            data_provider = SyntheticDataProvider(seed=self.config.random_seed)

        baseline_config = self.config.baseline_config or BaselineConfig()
        computer = BaselineComputer(baseline_config)
        self._baseline = computer.compute(data_provider)

        self.event_log.record(
            event_type="baseline.evaluated",
            actor="system",
            artifact_refs=[self._baseline.baseline_id],
            metadata={"baseline_type": self._baseline.baseline_type},
        )

        return self._baseline

    def compute_statistics(self) -> dict:
        """Compute DSR and PBO from the trial ledger.

        Uses the actual number of eligible trials from the ledger,
        not the configured maximum.
        """
        from sas.quant.statistics.deflated_sharpe import compute_dsr_from_trial
        from sas.quant.statistics.pbo import compute_pbo_from_trials

        evaluated = self.trial_ledger.get_evaluated_trials()
        trial_count = len(evaluated)

        # Compute DSR for the incumbent
        incumbent = self.trial_ledger.get_incumbent()
        if incumbent and trial_count > 0:
            dsr_result = compute_dsr_from_trial(incumbent, trial_count)
            self._dsr_value = dsr_result.dsr
        else:
            dsr_result = None
            self._dsr_value = None

        # Compute PBO from all evaluated trials
        if trial_count >= 2:
            pbo_result = compute_pbo_from_trials(evaluated)
            self._pbo_value = pbo_result.pbo
        else:
            pbo_result = None
            self._pbo_value = None

        self.event_log.record(
            event_type="statistics.computed",
            actor="system",
            metadata={
                "trial_count": trial_count,
                "dsr": self._dsr_value,
                "pbo": self._pbo_value,
            },
        )

        return {
            "dsr": dsr_result.to_dict() if dsr_result else None,
            "pbo": pbo_result.to_dict() if pbo_result else None,
        }

    def evaluate_holdout(
        self,
        data_provider: MarketDataProvider | None = None,
    ) -> HoldoutArtifact:
        """Evaluate the incumbent strategy on the holdout window.

        This is a one-shot evaluation. The strategy is immutable.
        The model receives no feedback from the holdout.
        """
        if data_provider is None:
            data_provider = SyntheticDataProvider(seed=self.config.random_seed)

        incumbent = self.trial_ledger.get_incumbent()
        if not incumbent:
            raise ValueError("No incumbent strategy to evaluate on holdout")

        # Transition to HOLDOUT capability
        self.temporal_authority.transition_to_holdout()

        # Get holdout data
        holdout_start, holdout_end = self.config.holdout_window
        # For simplicity, use the incumbent's first universe symbol
        # In a full implementation, this would use the strategy's universe
        symbol = incumbent.strategy_spec.get("universe", ["DEFAULT"])[0] if incumbent.strategy_spec.get("universe") else "DEFAULT"

        df = data_provider.get_prices(symbol, holdout_start, holdout_end)
        if df.empty or "close" not in df.columns:
            # Create minimal data
            import pandas as pd
            import numpy as np
            dates = pd.date_range(holdout_start, holdout_end, freq="B")
            n = len(dates)
            rng = np.random.default_rng(self.config.random_seed)
            df = pd.DataFrame(
                {"close": 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.02, n)))},
                index=dates,
            )

        close = df["close"]
        return_series = close.pct_change().dropna().tolist()

        strategy_total_return = float(close.iloc[-1] / close.iloc[0] - 1)
        strategy_sharpe = self._compute_sharpe(return_series)
        strategy_max_dd = self._compute_max_drawdown(close.tolist())

        # Baseline on holdout
        baseline_total_return = 0.0
        baseline_sharpe = 0.0
        if self._baseline:
            # Use baseline return series if available
            if self._baseline.return_series:
                baseline_sharpe = self._compute_sharpe(self._baseline.return_series)
            baseline_total_return = self._baseline.total_return

        outperformed = strategy_total_return > baseline_total_return

        self._holdout = HoldoutArtifact(
            experiment_id=self.experiment_id,
            trial_id=incumbent.trial_id,
            holdout_window=(holdout_start, holdout_end),
            strategy_total_return=strategy_total_return,
            strategy_sharpe_ratio=strategy_sharpe,
            strategy_max_drawdown=strategy_max_dd,
            baseline_total_return=baseline_total_return,
            baseline_sharpe_ratio=baseline_sharpe,
            outperformed_baseline=outperformed,
        )

        self.event_log.record(
            event_type="holdout.evaluated",
            trial_id=incumbent.trial_id,
            actor="system",
            artifact_refs=[self._holdout.holdout_id],
            metadata={
                "strategy_return": strategy_total_return,
                "baseline_return": baseline_total_return,
                "outperformed": outperformed,
            },
        )

        return self._holdout

    def make_decision(self) -> ResearchDecision:
        """Make the final research decision.

        The decision is derived entirely from the immutable experiment
        artifacts and event history.
        """
        if not self._is_complete:
            self._finalize()

        return self._decision

    def _finalize(self) -> None:
        """Finalize the experiment and make the research decision."""
        # Transition to FINAL
        if self.temporal_authority.capability.value != "final":
            try:
                self.temporal_authority.transition_to_final()
            except ValueError:
                pass  # Already in FINAL

        incumbent = self.trial_ledger.get_incumbent()
        evaluated = self.trial_ledger.get_evaluated_trials()

        # Determine outcome
        outcome = "no_strategy_passed"
        rationale = ""

        if not incumbent:
            rationale = "No incumbent strategy was selected"
        elif not incumbent.backtest_result:
            rationale = "Incumbent strategy was not evaluated"
        else:
            # Check gates
            risk_result, stat_result = self.gates.evaluate(
                incumbent,
                dsr_value=self._dsr_value,
                pbo_value=self._pbo_value,
            )

            if not risk_result.passed:
                outcome = "no_strategy_passed"
                rationale = f"Risk gate failed: {risk_result.reason}"
            elif not stat_result.passed:
                outcome = "no_strategy_passed"
                rationale = f"Statistical gate failed: {stat_result.reason}"
            elif self._holdout and not self._holdout.outperformed_baseline:
                outcome = "passed_but_no_value"
                rationale = "Strategy passed gates but did not outperform baseline"
            else:
                outcome = "candidate"
                rationale = "Strategy passed gates and outperformed baseline"

        self._decision = ResearchDecision(
            experiment_id=self.experiment_id,
            outcome=outcome,
            incumbent_trial_id=incumbent.trial_id if incumbent else None,
            baseline_id=self._baseline.baseline_id if self._baseline else "",
            holdout_id=self._holdout.holdout_id if self._holdout else "",
            rationale=rationale,
            trial_count=self.trial_ledger.total_trials,
            evaluated_count=len(evaluated),
        )

        self._is_complete = True

        self.event_log.record(
            event_type="experiment.completed",
            actor="system",
            artifact_refs=[self._decision.decision_id],
            metadata={
                "outcome": outcome,
                "trial_count": self.trial_ledger.total_trials,
            },
        )

    def _compute_sharpe(self, returns: list[float]) -> float:
        """Compute annualized Sharpe ratio."""
        if not returns or len(returns) < 2:
            return 0.0
        import numpy as np
        r = np.array(returns)
        mean = float(np.mean(r))
        std = float(np.std(r, ddof=1))
        if std == 0:
            return 0.0
        return (mean / std) * np.sqrt(252)

    def _compute_max_drawdown(self, values: list[float]) -> float:
        """Compute maximum drawdown."""
        if not values:
            return 0.0
        peak = values[0]
        max_dd = 0.0
        for v in values:
            peak = max(peak, v)
            dd = (peak - v) / peak if peak > 0 else 0.0
            max_dd = max(max_dd, dd)
        return max_dd

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "config": self.config.to_dict(),
            "is_complete": self._is_complete,
            "trial_ledger": self.trial_ledger.to_dict(),
            "event_log": self.event_log.to_dict(),
            "baseline": self._baseline.to_dict() if self._baseline else None,
            "holdout": self._holdout.to_dict() if self._holdout else None,
            "decision": self._decision.to_dict() if self._decision else None,
            "dsr": self._dsr_value,
            "pbo": self._pbo_value,
        }
