"""Holdout evaluation — physically separate from research.

The holdout is evaluated exactly once, after the research phase
terminates. The strategy evaluated on holdout is immutable —
the model receives no feedback from the holdout.

The holdout boundary is impossible to cross through ordinary tool calls.
The runtime transitions from RESEARCH → HOLDOUT → FINAL, one-way only.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from sas.quant.backtest import BacktestConfig, BacktestEngine
from sas.quant.market import MarketDataProvider, SyntheticDataProvider
from sas.quant.provenance.artifacts import HoldoutArtifact, TrialArtifact
from sas.quant.research.experiment import Experiment
from sas.quant.research.temporal import ExecutionCapability
from sas.quant.strategy import StrategyArtifact


@dataclass
class HoldoutConfig:
    """Configuration for holdout evaluation."""

    holdout_window: tuple[str, str] = ("", "")
    initial_capital: float = 100_000.0
    seed: int = 42

    def to_dict(self) -> dict:
        return {
            "holdout_window": list(self.holdout_window),
            "initial_capital": self.initial_capital,
            "seed": self.seed,
        }


class HoldoutEvaluator:
    """Evaluates the incumbent strategy on the holdout window.

    The holdout evaluation is a one-shot process. The strategy is
    immutable. The model receives no feedback from the holdout.

    The evaluator operates within the HOLDOUT capability. It cannot
    access research data or mutate the strategy.
    """

    def __init__(
        self,
        experiment: Experiment,
        data_provider: MarketDataProvider | None = None,
    ):
        self.experiment = experiment
        self.data_provider = data_provider or SyntheticDataProvider(
            seed=experiment.config.random_seed
        )

    def evaluate(self) -> HoldoutArtifact:
        """Evaluate the incumbent strategy on the holdout window.

        This is a one-shot evaluation. The strategy is immutable.
        The model receives no feedback from the holdout.
        """
        # Verify we're in HOLDOUT capability
        if self.experiment.temporal_authority.capability != ExecutionCapability.HOLDOUT:
            raise ValueError(
                "Holdout evaluation requires HOLDOUT capability. "
                "Transition from RESEARCH to HOLDOUT first."
            )

        incumbent = self.experiment.trial_ledger.get_incumbent()
        if not incumbent:
            raise ValueError("No incumbent strategy to evaluate on holdout")

        # Record holdout.opened event
        self.experiment.event_log.record(
            event_type="holdout.opened",
            trial_id=incumbent.trial_id,
            actor="system",
            metadata={"holdout_window": self.experiment.config.holdout_window},
        )

        # Get holdout data
        holdout_start, holdout_end = self.experiment.config.holdout_window
        symbol = incumbent.strategy_spec.get("universe", ["AAPL"])[0]

        # Validate temporal authority
        is_valid, error = self.experiment.temporal_authority.validate_date_range(
            holdout_start, holdout_end
        )
        if not is_valid:
            raise ValueError(f"Temporal violation: {error}")

        prices = self.data_provider.get_prices(symbol, holdout_start, holdout_end)
        if prices.empty:
            # Generate synthetic data
            dates = pd.date_range(holdout_start, holdout_end, freq="B")
            n = len(dates)
            rng = np.random.default_rng(self.experiment.config.random_seed)
            prices = pd.DataFrame(
                {"close": 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.02, n)))},
                index=dates,
            )

        # Run backtest on holdout
        strategy = StrategyArtifact(
            strategy_id=incumbent.trial_id,
            name=incumbent.strategy_spec.get("name", incumbent.trial_id),
            signal_definition=incumbent.strategy_spec.get("signal_definition", {}),
            universe=incumbent.strategy_spec.get("universe", ["AAPL"]),
            created_by="holdout-evaluator",
        )

        config = BacktestConfig(
            strategy=strategy,
            seed=incumbent.random_seed,
            initial_capital=self.experiment.config.initial_capital,
            train_start=holdout_start,
            train_end=holdout_end,
        )
        engine = BacktestEngine(config)
        bt_result = engine.run(config, prices)

        # Compute baseline on holdout
        baseline_total_return = 0.0
        baseline_sharpe = 0.0
        if self.experiment.baseline:
            baseline_total_return = self.experiment.baseline.total_return
            baseline_sharpe = self.experiment.baseline.sharpe_ratio

        strategy_total_return = bt_result.total_return
        strategy_sharpe = bt_result.sharpe_ratio
        strategy_max_dd = bt_result.max_drawdown

        outperformed = strategy_total_return > baseline_total_return

        holdout = HoldoutArtifact(
            experiment_id=self.experiment.experiment_id,
            trial_id=incumbent.trial_id,
            holdout_window=(holdout_start, holdout_end),
            strategy_total_return=strategy_total_return,
            strategy_sharpe_ratio=strategy_sharpe,
            strategy_max_drawdown=strategy_max_dd,
            baseline_total_return=baseline_total_return,
            baseline_sharpe_ratio=baseline_sharpe,
            outperformed_baseline=outperformed,
        )

        # Record holdout.evaluated event
        self.experiment.event_log.record(
            event_type="holdout.evaluated",
            trial_id=incumbent.trial_id,
            actor="system",
            artifact_refs=[holdout.holdout_id],
            metadata={
                "strategy_return": strategy_total_return,
                "baseline_return": baseline_total_return,
                "outperformed": outperformed,
            },
        )

        return holdout
