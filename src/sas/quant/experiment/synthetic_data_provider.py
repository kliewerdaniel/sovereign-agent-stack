"""Synthetic data provider that serves data from synthetic worlds.

This provider wraps a SyntheticWorld and serves its research/holdout data
through the MarketDataProvider interface. This allows the governed research
pipeline to run on synthetic worlds with known data generating processes.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from sas.quant.market import DatasetInfo, MarketDataProvider
from sas.quant.experiment.synthetic_worlds import SyntheticWorld


class SyntheticWorldProvider(MarketDataProvider):
    """Data provider that serves data from a SyntheticWorld.

    This provider wraps a SyntheticWorld and serves its research/holdout data
    through the MarketDataProvider interface. This allows the governed research
    pipeline to run on synthetic worlds with known data generating processes.
    """

    def __init__(self, world: SyntheticWorld, seed: int = 42):
        self._world = world
        self._seed = seed
        self._symbols = [world.symbol]
        self._version = "synthetic-world-1.0.0"

    def get_prices(self, symbol: str, start: str, end: str, include_signal: bool = False) -> pd.DataFrame:
        """Get price data for the given symbol and date range.

        This provider serves data for ANY symbol by mapping to the world's
        data. This is intentional: the synthetic world is a controlled
        experimental environment where the symbol is a label, not a real
        ticker. The researcher's hardcoded "AAPL"/"MSFT" symbols are
        mapped to the world's data.

        Args:
            symbol: Ticker symbol (ignored — maps to world's data)
            start: Start date string
            end: End date string
            include_signal: If True, include the signal column (for oracle).
                          If False, only return close and returns (for agent).
        """
        # Check if date range falls within research or holdout window
        research_start, research_end = self._world.research_window
        holdout_start, holdout_end = self._world.holdout_window

        if start >= research_start and end <= research_end:
            # Return research data
            mask = (
                (self._world.research_data.index >= pd.Timestamp(start))
                & (self._world.research_data.index <= pd.Timestamp(end))
            )
            data = self._world.research_data.loc[mask].copy()
        elif start >= holdout_start and end <= holdout_end:
            # Return holdout data
            mask = (
                (self._world.holdout_data.index >= pd.Timestamp(start))
                & (self._world.holdout_data.index <= pd.Timestamp(end))
            )
            data = self._world.holdout_data.loc[mask].copy()
        else:
            return pd.DataFrame()

        # Strip signal column unless explicitly requested
        if not include_signal and "signal" in data.columns:
            data = data.drop(columns=["signal"])

        return data

    def get_bars(self, symbol: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        """Get OHLCV bars for the given symbol and date range."""
        return self.get_prices(symbol, start, end)

    def validate(self, symbol: str, start: str, end: str) -> dict:
        """Validate the data request."""
        df = self.get_prices(symbol, start, end)
        return {
            "symbol": symbol,
            "valid": True,
            "issues": ["SYNTHETIC DATA — not for live trading"],
            "rows": len(df),
        }

    def source_info(self) -> DatasetInfo:
        """Get information about the data source."""
        return DatasetInfo(
            source="synthetic-world",
            version=self._version,
            symbols=self._symbols,
            start_date=self._world.research_window[0],
            end_date=self._world.holdout_window[1],
            row_count=len(self._world.research_data) + len(self._world.holdout_data),
            is_synthetic=True,
        )
