"""Pytest fixtures for Sovereign Quant tests."""

from __future__ import annotations

from io import StringIO

import pandas as pd
import pytest

from sas.quant.market.yfinance import YFinanceProvider, YFResultInfo
from sas.quant.market.stooq import StooqProvider
from sas.quant.market.alpaca import AlpacaProvider

# ── Shared mock CSV (used by yfinance, stooq, alpaca cache-persistence tests) ──

MOCK_CSV = "\n".join(
    [
        "Date,Open,High,Low,Close,Volume",
        "2024-01-02,184.895814,186.170285,183.404007,183.404007,82488700",
        "2024-01-03,182.001094,183.641103,182.030731,182.030731,58414500",
        "2024-01-04,179.956063,180.884744,179.718934,179.718934,71983600",
        "2024-01-05,179.797983,180.558698,178.997726,178.997726,62379700",
        "2024-01-08,179.896761,183.364966,179.538299,183.324997,59144500",
        "2024-01-09,183.220199,183.966003,182.455994,182.910049,58914500",
        "2024-01-10,183.980011,184.550011,183.010010,183.389999,61465500",
    ]
)


VALID_SYMBOLS = frozenset({"AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "META", "SPY", "QQQ", "IWM", "TLT", "SAP", "VOW3", "BMW", "Siemens"})


def _mock_yf_frame(symbol="AAPL"):
    if symbol not in VALID_SYMBOLS:
        return pd.DataFrame()
    df = pd.read_csv(StringIO(MOCK_CSV), parse_dates=["Date"], index_col="Date")
    out = pd.DataFrame(index=df.index)
    out.index.name = "Date"
    for col in ["open", "high", "low", "close", "volume"]:
        src = col.capitalize()
        out[col] = df[src].astype(float)
    out = out[out["close"].notna()]
    return out


def _mock_stooq_frame(symbol="AAPL"):
    return _mock_yf_frame(symbol)


def _mock_alpaca_frame(symbol="AAPL"):
    return _mock_yf_frame(symbol)


@pytest.fixture
def mock_yf_download(monkeypatch):
    """Monkeypatch YFinanceProvider._download_one to return MOCK_CSV data,
    returning empty frames for unknown symbols."""
    monkeypatch.setattr(
        YFinanceProvider, "_download_one",
        lambda self, symbol, start, end: _mock_yf_frame(symbol),
    )
    return lambda symbol: _mock_yf_frame(symbol)


@pytest.fixture
def yf_provider(mock_yf_download):
    """A YFinanceProvider with mocked _download_one, pre-populated cache."""
    prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
    prov.download_all()
    return prov


@pytest.fixture
def mock_stooq_download(monkeypatch):
    """Monkeypatch StooqProvider._download_one to return MOCK_CSV data,
    returning empty frames for unknown symbols."""
    def _fake(self, symbol, start, end, requests_mod):
        return _mock_stooq_frame(symbol)

    monkeypatch.setattr(StooqProvider, "_download_one", _fake)
    return _fake


@pytest.fixture
def stooq_provider(mock_stooq_download):
    """A StooqProvider with mocked _download_one, pre-populated cache."""
    prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
    prov.download_all()
    return prov


@pytest.fixture
def mock_alpaca_download(monkeypatch):
    """Monkeypatch AlpacaProvider._download_one to return MOCK_CSV data,
    returning empty frames for unknown symbols."""
    monkeypatch.setattr(
        AlpacaProvider, "_download_one",
        lambda self, symbol, start, end: _mock_alpaca_frame(symbol),
    )
    return lambda symbol: _mock_alpaca_frame(symbol)


@pytest.fixture
def alpaca_provider(mock_alpaca_download):
    """An AlpacaProvider with mocked _download_one, pre-populated cache."""
    prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                          key_id="x", secret_key="y")
    prov.download_all()
    return prov
