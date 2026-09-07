"""Researcher — the research loop controller.

The researcher drives the experiment by running the multi-trial research
loop. It is the ONLY component that can create new trials, invoke the
model, and transition the experiment state.

The research loop:
  for trial in range(budget):
    1. Model proposes a strategy (or revises from critique)
    2. System records the trial in the ledger
    3. System backtests the strategy
    4. System records the backtest result
    5. Model produces a critique (bounded reflection)
    6. If critique recommends revision → new trial (parent-child link)
    7. Check stopping criteria

The researcher operates within the RESEARCH capability. It cannot
access holdout data or mutate completed trials.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from sas.quant.backtest import BacktestConfig, BacktestEngine, BacktestResult
from sas.quant.market import MarketDataProvider, SyntheticDataProvider
from sas.quant.provenance.artifacts import CritiqueArtifact, TrialArtifact
from sas.quant.research.experiment import Experiment, ExperimentConfig
from sas.quant.research.reflection import BoundedReflector
from sas.quant.research.temporal import ExecutionCapability
from sas.quant.strategy import (
    PositionSizing,
    SignalDefinition,
    StrategyArtifact,
)
from sas.quant.toolbox import create_toolbox_from_world
from sas.quant.world import (
    ExecutionRun,
    QuantWorld,
    QuantWorldBuilder,
    Task,
)


@dataclass
class ResearchResult:
    """Result of a research loop execution."""

    experiment: Experiment
    incumbent: TrialArtifact | None = None
    total_trials: int = 0
    evaluated_trials: int = 0
    status: str = "pending"
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment.experiment_id,
            "incumbent_id": self.incumbent.trial_id if self.incumbent else None,
            "total_trials": self.total_trials,
            "evaluated_trials": self.evaluated_trials,
            "status": self.status,
            "errors": list(self.errors),
        }


class Researcher:
    """Drives the multi-trial research loop.

    The researcher is the only component that can create new trials.
    It operates within the RESEARCH capability and cannot access
    holdout data or mutate completed trials.
    """

    def __init__(
        self,
        experiment: Experiment,
        data_provider: MarketDataProvider | None = None,
        model_config: dict | None = None,
    ):
        self.experiment = experiment
        self.data_provider = data_provider or SyntheticDataProvider(
            seed=experiment.config.random_seed
        )
        self.model_config = model_config or {
            "provider": "stub",
            "name": "stub-model",
        }
        self.reflector = BoundedReflector(
            max_reflection_rounds=experiment.config.max_reflection_rounds
        )

    def run_research(self) -> ResearchResult:
        """Run the full research loop.

        Proposes strategies, backtests them, records trials, and
        manages the trial budget.
        """
        result = ResearchResult(experiment=self.experiment)

        # Record research start
        self.experiment.event_log.record(
            event_type="research.started",
            actor="researcher",
            metadata={
                "trial_budget": self.experiment.config.trial_budget,
                "research_window": self.experiment.config.research_window,
            },
        )

        trial_count = 0
        incumbent: TrialArtifact | None = None

        while trial_count < self.experiment.config.trial_budget:
            # Check if we're still in RESEARCH capability
            if self.experiment.temporal_authority.capability != ExecutionCapability.RESEARCH:
                result.errors.append("Research capability has been terminated")
                break

            # Run a single trial
            trial = self._run_single_trial(trial_count, incumbent)
            trial_count += 1

            if trial is None:
                continue

            # Update incumbent if this trial is better
            if trial.was_evaluated and trial.sharpe_ratio is not None and not np.isnan(trial.sharpe_ratio):
                if incumbent is None or (
                    incumbent.sharpe_ratio is not None
                    and trial.sharpe_ratio > incumbent.sharpe_ratio
                ):
                    incumbent = trial
                    self.experiment.trial_ledger.set_incumbent(trial.trial_id)

            # Check for revision
            if trial.critique_id:
                critique = self._get_critique(trial.critique_id)
                if critique and critique.recommendation == "revise":
                    # Revision creates a new trial (handled in next iteration)
                    self.experiment.event_log.record(
                        event_type="trial.revised",
                        trial_id=trial.trial_id,
                        actor="model",
                        artifact_refs=[critique.critique_id],
                        metadata={"parent_trial_id": trial.trial_id},
                    )

        # Research terminated
        self.experiment.event_log.record(
            event_type="research.terminated",
            actor="researcher",
            metadata={
                "total_trials": trial_count,
                "evaluated_trials": self.experiment.trial_ledger.evaluated_count,
            },
        )

        result.incumbent = incumbent
        result.total_trials = trial_count
        result.evaluated_trials = self.experiment.trial_ledger.evaluated_count
        result.status = "completed"

        return result

    def _run_single_trial(
        self,
        trial_number: int,
        parent_trial: TrialArtifact | None = None,
    ) -> TrialArtifact | None:
        """Run a single trial: propose → backtest → critique."""
        # Build a simple strategy spec for this trial
        strategy_spec = self._build_strategy_spec(trial_number, parent_trial)

        # Record the trial in the ledger
        trial = self.experiment.trial_ledger.record_trial(
            strategy_spec=strategy_spec,
            model_id=self.model_config.get("name", "stub-model"),
            task_id=self.experiment.config.task_id,
            data_window=self.experiment.config.research_window,
            random_seed=self.experiment.config.random_seed + trial_number,
            parameterization={"trial_number": trial_number},
            parent_trial_id=parent_trial.trial_id if parent_trial else None,
        )

        # Record trial.proposed event
        self.experiment.event_log.record(
            event_type="trial.proposed",
            trial_id=trial.trial_id,
            actor="model",
            metadata={"trial_number": trial_number},
        )

        # Run backtest
        try:
            backtest_result = self._run_backtest(trial, strategy_spec)
            return_series = backtest_result.get("monthly_returns", [])

            # record_backtest_result returns the authoritative updated trial
            trial = self.experiment.trial_ledger.record_backtest_result(
                trial_id=trial.trial_id,
                backtest_result=backtest_result,
                return_series=return_series,
            )

            # Record backtest.completed event
            self.experiment.event_log.record(
                event_type="backtest.completed",
                trial_id=trial.trial_id,
                actor="system",
                metadata={"sharpe_ratio": backtest_result.get("sharpe_ratio")},
            )

        except Exception as e:
            self.experiment.trial_ledger.record_rejection(
                trial_id=trial.trial_id,
                reason=f"Backtest failed: {str(e)}",
            )
            return trial

        # Bounded reflection
        try:
            critique = self._run_critique(trial, backtest_result)
            if critique:
                self.experiment.trial_ledger.link_critique(
                    trial_id=trial.trial_id,
                    critique_id=critique.critique_id,
                )
                # Record critique.created event
                self.experiment.event_log.record(
                    event_type="critique.created",
                    trial_id=trial.trial_id,
                    actor="model",
                    artifact_refs=[critique.critique_id],
                    metadata={
                        "recommendation": critique.recommendation,
                        "severity": critique.severity,
                    },
                )
        except Exception as e:
            # Critique failure is non-fatal
            pass

        return trial

    def _build_strategy_spec(
        self,
        trial_number: int,
        parent_trial: TrialArtifact | None = None,
    ) -> dict:
        """Build a strategy spec for a trial.

        In a full implementation, this would invoke the model to propose
        a strategy. For now, we generate deterministic variations.
        """
        import numpy as np

        rng = np.random.default_rng(self.experiment.config.random_seed + trial_number)
        signal_types = ["momentum", "mean_reversion", "trend", "volatility"]
        signal_type = signal_types[rng.integers(0, len(signal_types))]

        return {
            "name": f"trial-{trial_number}-{signal_type}",
            "signal_name": signal_type,
            "signal_type": signal_type,
            "signal_params": {
                "lookback": int(rng.integers(10, 252)),
                "skip": int(rng.integers(1, 21)),
            },
            "sizing_method": "fixed_weight",
            "target_weight": 0.10,
            "max_position": 0.25,
            "rebalance_frequency": "monthly",
            "universe": ["AAPL", "MSFT"],
        }

    def _run_backtest(
        self,
        trial: TrialArtifact,
        strategy_spec: dict,
    ) -> dict:
        """Run a backtest for a trial."""
        # Get price data within the research window
        start, end = self.experiment.config.research_window
        symbol = strategy_spec.get("universe", ["AAPL"])[0]

        # Validate temporal authority
        is_valid, error = self.experiment.temporal_authority.validate_date_range(start, end)
        if not is_valid:
            raise ValueError(f"Temporal violation: {error}")

        prices = self.data_provider.get_prices(symbol, start, end)
        if prices.empty:
            # Generate synthetic data
            import pandas as pd
            import numpy as np
            dates = pd.date_range(start, end, freq="B")
            n = len(dates)
            rng = np.random.default_rng(trial.random_seed)
            prices = pd.DataFrame(
                {"close": 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.02, n)))},
                index=dates,
            )

        strategy = StrategyArtifact(
            strategy_id=trial.trial_id,
            name=strategy_spec.get("name", trial.trial_id),
            signal_definition=SignalDefinition(
                name=strategy_spec.get("signal_name", "momentum"),
                type=strategy_spec.get("signal_type", "momentum"),
                parameters=strategy_spec.get("signal_params", {}),
            ),
            universe=strategy_spec.get("universe", ["AAPL"]),
            position_sizing=PositionSizing(
                method=strategy_spec.get("sizing_method", "fixed_weight"),
                target_weight=strategy_spec.get("target_weight", 0.10),
            ),
            created_by="researcher",
        )

        config = BacktestConfig(
            strategy=strategy,
            seed=trial.random_seed,
            initial_capital=self.experiment.config.initial_capital,
            train_start=start,
            train_end=end,
            test_start=start,
            test_end=end,
        )
        engine = BacktestEngine(config)
        bt_result = engine.run(config, prices)

        return bt_result.to_dict()

    def _run_critique(
        self,
        trial: TrialArtifact,
        backtest_result: dict,
    ) -> CritiqueArtifact | None:
        """Run a bounded reflection step.

        The model critiques its own strategy. The critique is a
        structured artifact.
        """
        # In a full implementation, this would invoke the model.
        # For now, generate a deterministic critique based on results.
        sharpe = backtest_result.get("sharpe_ratio", 0.0)
        max_dd = backtest_result.get("max_drawdown", 0.0)

        weaknesses = []
        if sharpe < 0.5:
            weaknesses.append({
                "name": "low_sharpe",
                "severity": "high",
                "evidence": f"Sharpe ratio {sharpe:.4f} is below 0.5",
            })
        if abs(max_dd) > 0.20:
            weaknesses.append({
                "name": "high_drawdown",
                "severity": "medium",
                "evidence": f"Max drawdown {abs(max_dd):.2%} exceeds 20%",
            })

        recommendation = "accept" if not weaknesses else "revise"

        critique = self.reflector.create_critique(
            trial_id=trial.trial_id,
            experiment_id=self.experiment.experiment_id,
            weaknesses=weaknesses,
            severity="high" if any(w["severity"] == "high" for w in weaknesses) else "low",
            evidence=[w["evidence"] for w in weaknesses],
            recommendation=recommendation,
            action=recommendation,
            reasoning=f"Auto-critique: {len(weaknesses)} weaknesses found",
            parent_trial_id=trial.parent_trial_id,
        )

        return critique

    def _get_critique(self, critique_id: str) -> CritiqueArtifact | None:
        """Retrieve a critique artifact by ID."""
        # In a full implementation, this would retrieve from a store.
        # For now, return None (the critique is embedded in the trial).
        return None
