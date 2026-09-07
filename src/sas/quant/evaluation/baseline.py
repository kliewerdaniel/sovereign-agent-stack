"""Mandatory baseline for every QuantWorld.

Every experiment must produce a baseline. The baseline is defined by the
world or experiment configuration — it is not hardcoded. For an equity
universe, this is typically an equally weighted buy-and-hold of the
available universe. The abstraction supports a designated benchmark
(e.g. SPY) when the world explicitly defines one.

The baseline uses the same permitted temporal boundaries and transaction
cost assumptions as the strategy where applicable.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional

import numpy as np
import pandas as pd

from sas.quant.market import MarketDataProvider, SyntheticDataProvider
from sas.quant.provenance.artifacts import BaselineArtifact


@dataclass(frozen=True)
class BaselineConfig:
    """Configuration for the baseline computation."""

    baseline_type: str = "buy_and_hold"  # buy_and_hold | designated_benchmark
    benchmark_symbol: str | None = None  # e.g. "SPY" if designated
    universe: list[str] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)
    data_window: tuple[str, str] = ("", "")
    initial_capital: float = 100_000.0
    transaction_cost_bps: float = 0.0  # basis points per trade
    seed: int = 42

    def to_dict(self) -> dict:
        return {
            "baseline_type": self.baseline_type,
            "benchmark_symbol": self.benchmark_symbol,
            "universe": list(self.universe),
            "weights": dict(self.weights),
            "data_window": list(self.data_window),
            "initial_capital": self.initial_capital,
            "transaction_cost_bps": self.transaction_cost_bps,
            "seed": self.seed,
        }


class BaselineComputer:
    """Computes the mandatory baseline for a QuantWorld.

    The baseline is a first-class artifact of every experiment. It is
    computed from the world definition and uses the same temporal
    boundaries as the research phase.
    """

    def __init__(self, config: BaselineConfig):
        self.config = config

    def compute(
        self,
        data_provider: MarketDataProvider | None = None,
    ) -> BaselineArtifact:
        """Compute the baseline artifact.

        Args:
            data_provider: Market data provider. If None, uses SyntheticProvider.

        Returns:
            BaselineArtifact with full provenance.
        """
        if data_provider is None:
            data_provider = SyntheticDataProvider(seed=self.config.seed)

        if self.config.baseline_type == "designated_benchmark" and self.config.benchmark_symbol:
            return self._compute_designated_benchmark(data_provider)
        else:
            return self._compute_buy_and_hold(data_provider)

    def _compute_buy_and_hold(
        self,
        data_provider: MarketDataProvider,
    ) -> BaselineArtifact:
        """Compute equally weighted buy-and-hold baseline."""
        universe = self.config.universe
        if not universe:
            return self._empty_baseline()

        # Equal weights if not specified
        weights = self.config.weights
        if not weights:
            n = len(universe)
            weights = {sym: 1.0 / n for sym in universe}

        # Get price data for each symbol
        start, end = self.config.data_window
        price_data = {}
        for sym in universe:
            df = data_provider.get_prices(sym, start, end)
            if not df.empty and "close" in df.columns:
                price_data[sym] = df["close"]

        if not price_data:
            return self._empty_baseline()

        # Align all series
        df = pd.DataFrame(price_data)
        df = df.dropna()
        if len(df) < 2:
            return self._empty_baseline()

        # Compute portfolio returns
        normalized = df.div(df.iloc[0])  # Normalize to 1.0 at start
        weighted = normalized.mul([weights.get(sym, 0) for sym in normalized.columns])
        portfolio_value = weighted.sum(axis=1)
        return_series = portfolio_value.pct_change().dropna().tolist()

        # Compute metrics
        total_return = float(portfolio_value.iloc[-1] / portfolio_value.iloc[0] - 1)
        sharpe = self._compute_sharpe(return_series)
        max_dd = self._compute_max_drawdown(portfolio_value.tolist())
        volatility = float(np.std(return_series, ddof=1) * np.sqrt(252)) if return_series else 0.0

        # Transaction costs (one-time entry)
        transaction_costs = self.config.initial_capital * self.config.transaction_cost_bps / 10000

        return BaselineArtifact(
            baseline_id=str(uuid.uuid4())[:12],
            experiment_id="",
            baseline_type="buy_and_hold",
            universe=list(universe),
            weights=weights,
            data_window=(start, end),
            total_return=total_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            volatility=volatility,
            return_series=return_series,
            transaction_costs=transaction_costs,
        )

    def _compute_designated_benchmark(
        self,
        data_provider: MarketDataProvider,
    ) -> BaselineArtifact:
        """Compute a designated benchmark baseline (e.g. SPY)."""
        symbol = self.config.benchmark_symbol
        if not symbol:
            return self._empty_baseline()

        start, end = self.config.data_window
        df = data_provider.get_prices(symbol, start, end)
        if df.empty or "close" not in df.columns:
            return self._empty_baseline()

        close = df["close"]
        return_series = close.pct_change().dropna().tolist()

        total_return = float(close.iloc[-1] / close.iloc[0] - 1)
        sharpe = self._compute_sharpe(return_series)
        max_dd = self._compute_max_drawdown(close.tolist())
        volatility = float(np.std(return_series, ddof=1) * np.sqrt(252)) if return_series else 0.0

        transaction_costs = self.config.initial_capital * self.config.transaction_cost_bps / 10000

        return BaselineArtifact(
            baseline_id=str(uuid.uuid4())[:12],
            experiment_id="",
            baseline_type="designated_benchmark",
            benchmark_symbol=symbol,
            universe=[symbol],
            weights={symbol: 1.0},
            data_window=(start, end),
            total_return=total_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            volatility=volatility,
            return_series=return_series,
            transaction_costs=transaction_costs,
        )

    def _empty_baseline(self) -> BaselineArtifact:
        """Return an empty baseline when data is unavailable."""
        return BaselineArtifact(
            baseline_id=str(uuid.uuid4())[:12],
            experiment_id="",
            baseline_type=self.config.baseline_type,
            benchmark_symbol=self.config.benchmark_symbol,
            universe=list(self.config.universe),
            weights=dict(self.config.weights),
            data_window=self.config.data_window,
        )

    def _compute_sharpe(self, returns: list[float]) -> float:
        """Compute annualized Sharpe ratio."""
        if not returns or len(returns) < 2:
            return 0.0
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
