"""Market data provider abstraction.

Supports local providers (CSV, Parquet, SQLite).
External APIs are adapters.
All data is treated as untrusted input.
"""
from __future__ import annotations

import csv
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

__all__ = [
    "DatasetInfo",
    "LocalCSVDataset",
    "MarketDataPoint",
    "MarketDataProvider",
    "SyntheticDataProvider",
]


class MarketDataPoint:
    """Single market data point."""
    symbol: str
    date: str
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    adjusted_close: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class DatasetInfo:
    """Information about a dataset."""
    source: str
    version: str
    symbols: list[str]
    start_date: str
    end_date: str
    row_count: int
    is_synthetic: bool = False
    checksum: str = ""
    provenance: dict = field(default_factory=dict)


class MarketDataProvider(ABC):
    """Abstract base for market data providers."""

    @abstractmethod
    def get_prices(self, symbol: str,
                   start: str, end: str) -> pd.DataFrame:
        """Get price data for a symbol."""
        ...

    @abstractmethod
    def get_bars(self, symbol: str,
                 start: str, end: str,
                 interval: str = "1d") -> pd.DataFrame:
        """Get bar data for a symbol."""
        ...

    @abstractmethod
    def validate(self, symbol: str,
                 start: str, end: str) -> dict:
        """Validate data quality."""
        ...

    @abstractmethod
    def source_info(self) -> DatasetInfo:
        """Get information about the data source."""
        ...


class LocalCSVDataset(MarketDataProvider):
    """Local CSV market data provider."""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self._cache: dict[str, pd.DataFrame] = {}

    def get_prices(self, symbol: str,
                   start: str, end: str) -> pd.DataFrame:
        path = self.data_dir / f"{symbol}.csv"
        if not path.exists():
            return pd.DataFrame()
        df = pd.read_csv(path, parse_dates=["date"])
        df = df.set_index("date")
        return df.loc[start:end]

    def get_bars(self, symbol: str, start: str, end: str,
                   interval: str = "1d") -> pd.DataFrame:
        return self.get_prices(symbol, start, end)

    def validate(self, symbol: str,
                 start: str, end: str) -> dict:
        df = self.get_prices(symbol, start, end)
        issues = []
        if df.empty:
            issues.append("No data found")
        if df.isnull().any().any():
            issues.append("Contains null values")
        if (df["high"] < df["low"]).any():
            issues.append("High < Low violations")
        return {"symbol": symbol, "valid": len(issues) == 0,
                "issues": issues, "rows": len(df)}

    def source_info(self) -> DatasetInfo:
        return DatasetInfo(
            source="local_csv", version="1.0.0",
            symbols=[], start_date="", end_date="",
            row_count=0,
        )


class SyntheticDataProvider(MarketDataProvider):
    """Synthetic data generator for testing.

    IMPORTANT: All data from this provider is SYNTHETIC.
    Not for live trading.
    """

    def __init__(self, seed: int = 42):
        self._rng = np.random.default_rng(seed)
        self._symbols = ["AAPL", "MSFT", "GOOG", "AMZN", "META"]
        self._version = "synthetic-1.0.0"

    def get_prices(self, symbol: str,
                   start: str, end: str) -> pd.DataFrame:
        dates = pd.date_range(start, end, freq="B")
        n = len(dates)
        if n == 0:
            return pd.DataFrame()

        # Generate random walk
        returns = self._rng.normal(0.0005, 0.02, n)
        prices = 100 * np.exp(np.cumsum(returns))
        volumes = self._rng.lognormal(20, 1, n)

        df = pd.DataFrame({
            "open": prices * (1 + self._rng.normal(0, 0.005, n)),
            "high": prices * (1 + abs(self._rng.normal(0, 0.01, n))),
            "low": prices * (1 - abs(self._rng.normal(0, 0.01, n))),
            "close": prices,
            "volume": volumes,
        }, index=dates)
        df.index.name = "date"
        return df

    def get_bars(self, symbol: str, start: str, end: str,
                   interval: str = "1d") -> pd.DataFrame:
        return self.get_prices(symbol, start, end)

    def validate(self, symbol: str,
                 start: str, end: str) -> dict:
        df = self.get_prices(symbol, start, end)
        return {"symbol": symbol, "valid": True,
                "issues": ["SYNTHETIC DATA — not for live trading"],
                "rows": len(df)}

    def source_info(self) -> DatasetInfo:
        return DatasetInfo(
            source="synthetic", version=self._version,
            symbols=self._symbols, start_date="", end_date="",
            row_count=0, is_synthetic=True,
        )