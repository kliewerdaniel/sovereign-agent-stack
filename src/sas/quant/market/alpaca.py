"""
Alpaca market data provider for Sovereign Quant.

Backed by the Alpaca Market Data API (paper or live).  Requires a valid
Alpaca account with market data subscriptions enabled.  Credentials are
passed at construction time; the provider fails closed (empty frames +
honest validation) when credentials are absent or rejected.

Supports only daily (``1d``) bars through the ``MarketDataProvider``
interface.  All external data is treated as untrusted — always call
``validate()`` before use.
"""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import requests as _requests

from sas.quant.market import MarketDataProvider, MarketDataPoint, DatasetInfo

ALPCA_DATA_BASE = "https://data.alpaca.markets"


def _alpaca_symbol(symbol: str) -> str:
    """Normalise a symbol for the Alpaca Data API v2.

    Alpaca Data API v2 expects exchange-suffixed symbols for US equities
    (e.g. ``AAPL`` → ``AAPL/US``).  We only apply the suffix for common
    US tickers; everything else is passed through as-is.
    """
    s = symbol.upper().strip()
    if "/" not in s and "." not in s:
        return f"{s}/US"
    return s


@dataclass
class AlpacaResultInfo:
    """Metadata returned by an Alpaca bulk download for provenance."""

    symbols: list[str]
    start: str
    end: str
    rows_per_symbol: dict[str, int]
    source: str = "alpaca"
    version: str = "1.0.0"
    downloaded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash:
            raw = {
                "symbols": tuple(self.symbols),
                "start": self.start,
                "end": self.end,
                "rows_per_symbol": dict(sorted(self.rows_per_symbol.items())),
            }
            self.content_hash = hashlib.sha256(str(raw).encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "version": self.version,
            "symbols": self.symbols,
            "start_date": self.start,
            "end_date": self.end,
            "row_count": sum(self.rows_per_symbol.values()),
            "rows_per_symbol": self.rows_per_symbol,
            "checksum": self.content_hash,
            "provenance": {
                "downloaded_at": self.downloaded_at,
                "content_hash": self.content_hash,
            },
        }


class AlpacaProvider(MarketDataProvider):
    """Market data provider backed by the Alpaca Data API v2.

    Requires an Alpaca account.  Pass ``key_id`` and ``secret_key`` (paper
    or live) at construction; leave them blank only for smoke-test scenarios
    where you expect empty frames.

    IMPORTANT: Alpaca data requires an active market data subscription.  The
    provider fails closed — empty frames and honest validation — rather than
    fabricating rows.
    """

    def __init__(
        self,
        symbols: list[str],
        start: str = "2024-01-02",
        end: str = "2024-12-31",
        key_id: str = "",
        secret_key: str = "",
        paper: bool = True,
        cache_dir: Optional[Path] = None,
    ):
        self._symbols: list[str] = list(symbols)
        self._start: str = start
        self._end: str = end
        self._key_id: str = key_id
        self._secret_key: str = secret_key
        self._paper: bool = paper
        self._base_url: str = (
            "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"
        )
        self._cache_dir: Path = cache_dir or Path.home() / ".sas" / "alpaca_cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._result_info: Optional[AlpacaResultInfo] = None

    # ── MarketDataProvider interface ──────────────────────────────────────

    def get_prices(self, symbol: str, start: str, end: str) -> "pd.DataFrame":
        """Return OHLCV DataFrame for *symbol* in [*start*, *end*]."""
        df = self._load_or_fetch(symbol)
        if df.empty:
            return df
        mask = (df.index >= start) & (df.index <= end)
        window = df[mask]
        return window  # type: ignore[return-value]

    def get_bars(
        self, symbol: str, start: str, end: str, interval: str = "1d"
    ) -> "pd.DataFrame":
        """Return bar data — only daily (``1d``) is supported."""
        if interval != "1d":
            return pd.DataFrame()
        return self.get_prices(symbol, start, end)

    def validate(self, symbol: str, start: str, end: str) -> dict:
        """Validate data quality for *symbol* in [*start*, *end*]."""
        df = self.get_prices(symbol, start, end)
        issues: list[str] = []
        if df.empty:
            issues.append("No data found")
            return {
                "symbol": symbol,
                "valid": False,
                "issues": issues,
                "rows": 0,
            }
        if df.isnull().any().any():
            issues.append("Contains null values")
        if "high" in df.columns and "low" in df.columns:
            if (df["high"] < df["low"]).any():
                issues.append("High < Low violations")
        return {
            "symbol": symbol,
            "valid": len(issues) == 0,
            "issues": issues,
            "rows": len(df),
        }

    def source_info(self) -> DatasetInfo:
        """Return dataset metadata from the most recent bulk download."""
        if self._result_info is None:
            self.download_all(self._symbols, self._start, self._end)
        info = self._result_info
        if info is None:
            return DatasetInfo(
                source="alpaca",
                version="1.0.0",
                symbols=[],
                start_date="",
                end_date="",
                row_count=0,
            )
        return DatasetInfo(
            source=info.source,
            version=info.version,
            symbols=info.symbols,
            start_date=info.start,
            end_date=info.end,
            row_count=sum(info.rows_per_symbol.values()),
            checksum=info.content_hash,
            provenance=info.to_dict()["provenance"],
        )

    # ── Bulk helpers ──────────────────────────────────────────────────────

    def download_all(
        self, symbols: Optional[list[str]] = None, start: str = "",
        end: str = "", _fetch_fresh: bool = False,
    ) -> AlpacaResultInfo:
        """Download (or reload from cache) OHLCV for *symbols*.

        Returns an ``AlpacaResultInfo`` with provenance metadata.  When
        ``_fetch_fresh`` is True, re-downloads even cached symbols (used by
        tests that want to observe a live fetch).
        """
        syms = symbols or self._symbols
        s = start or self._start
        e = end or self._end

        rows_per_symbol: dict[str, int] = {}
        downloaded_at = datetime.now(timezone.utc).isoformat()

        for sym in syms:
            path = self._cache_dir / f"{sym}.csv"
            if not _fetch_fresh and path.exists():
                try:
                    df = pd.read_csv(path, parse_dates=["Date"], index_col="Date")
                    if not df.empty:
                        rows_per_symbol[sym] = len(df)
                        continue
                except Exception:
                    pass  # re-fetch below

            df = self._download_one(sym, s, e)
            if df.empty:
                rows_per_symbol[sym] = 0
                continue
            self._persist(sym, df)
            rows_per_symbol[sym] = len(df)

        res = AlpacaResultInfo(
            symbols=syms,
            start=s,
            end=e,
            rows_per_symbol=rows_per_symbol,
            downloaded_at=downloaded_at,
        )
        self._result_info = res
        return res

    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """Remove cached CSV for *symbol* (or all symbols if None)."""
        if symbol:
            (self._cache_dir / f"{symbol}.csv").unlink(missing_ok=True)
        else:
            for p in self._cache_dir.glob("*.csv"):
                p.unlink(missing_ok=True)

    # ── Internals ─────────────────────────────────────────────────────────

    def _download_one(self, symbol: str, start: str, end: str) -> "pd.DataFrame":
        """One-symbol download from the Alpaca Data API v2 daily bars endpoint."""
        url = f"{self._base_url}/v2/stocks/{_alpaca_symbol(symbol)}/bars"
        params: dict[str, str] = {
            "timeframe": "1Day",
            "start": start,
            "end": end,
            "limit": "10000",
            "adjustment": "raw",
        }
        headers: dict[str, str] = {}
        if self._key_id and self._secret_key:
            cred = base64.b64encode(f"{self._key_id}:{self._secret_key}".encode()).decode()
            headers["Authorization"] = f"Basic {cred}"

        try:
            r = _requests.get(url, params={k: v for k, v in params.items() if v},
                              headers=headers, timeout=40)
        except Exception as e:
            print(f"[alpaca] fetch error {symbol}: {type(e).__name__}: {e}")
            return pd.DataFrame()

        if r.status_code != 200:
            body = r.text[:120].replace("\n", " ")
            print(f"[alpaca] non-200 {symbol}: {r.status_code} {body}")
            return pd.DataFrame()

        try:
            data = r.json()
        except Exception:
            print(f"[alpaca] non-json {symbol}: len={len(r.text)} head={r.text[:120]!r}")
            return pd.DataFrame()

        bars = data.get("bars") or []
        if not bars:
            return pd.DataFrame()

        df = pd.DataFrame(bars)
        if "t" in df.columns:
            df["t"] = pd.to_datetime(df["t"], unit="ns", errors="coerce")
            df = df.dropna(subset=["t"]).set_index("t")
        elif "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")
        else:
            return pd.DataFrame()

        df.index.name = "Date"
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                df[col] = float("nan")
        out = df[["open", "high", "low", "close", "volume"]].astype(float)
        return out

    def _load_or_fetch(self, symbol: str) -> "pd.DataFrame":
        """Load from cache or fetch fresh — caller already filtered by symbol."""
        path = self._cache_dir / f"{symbol}.csv"
        if path.exists():
            try:
                df = pd.read_csv(path, parse_dates=["Date"], index_col="Date")
                if not df.empty:
                    return df
            except Exception:
                pass
        return self._download_one(symbol, self._start, self._end)

    def _persist(self, symbol: str, df: pd.DataFrame) -> None:
        """Write *df* to cache as CSV; normalise to tz-naive UTC."""
        out = df.copy()
        if out.index.tz is not None:
            out.index = out.index.tz_convert("UTC").tz_localize(None)
        path = self._cache_dir / f"{symbol}.csv"
        out.to_csv(path, date_format="%Y-%m-%d %H:%M:%S")
