"""
YFinance market data provider for Sovereign Quant.

An adapter over the unofficial Yahoo Finance API.  Data is cached locally
under ``~/.sas/yf_cache/`` so repeated runs don't re-fetch.  Treat all
external data as untrusted — always call ``validate()`` before use.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from sas.quant.market import MarketDataProvider, MarketDataPoint, DatasetInfo


YFCACHE = Path.home() / ".sas" / "yf_cache"
YFCACHE.mkdir(parents=True, exist_ok=True)


@dataclass
class YFResultInfo:
    """Metadata returned by a yfinance bulk download for provenance."""

    symbols: list[str]
    start: str
    end: str
    rows_per_symbol: dict[str, int]
    source: str = "yfinance"
    version: str = "1.0.0"
    downloaded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash:
            # Hash only the data identity — symbols, window, and row counts.
            # downloaded_at is provenance metadata, not part of the content identity.
            raw = {
                "symbols": tuple(self.symbols),
                "start": self.start,
                "end": self.end,
                "rows_per_symbol": dict(sorted(self.rows_per_symbol.items())),
            }
            self.content_hash = hashlib.sha256(
                str(raw).encode()
            ).hexdigest()[:16]

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


class YFinanceProvider(MarketDataProvider):
    """Market data provider backed by yfinance.

    Downloads daily OHLCV bars for a list of symbols, caches them locally
    under ``~/.sas/yf_cache/<symbol>.csv``, and serves them through the
    MarketDataProvider interface.

    IMPORTANT: yfinance is an unofficial Yahoo Finance API.  Data quality
    varies — always call ``validate()`` before trusting results.
    """

    def __init__(
        self,
        symbols: list[str],
        start: str = "2024-01-02",
        end: str = "2024-12-31",
        auto_adjust: bool = True,
        cache_dir: Optional[Path] = None,
    ):
        self._symbols: list[str] = list(symbols)
        self._start: str = start
        self._end: str = end
        self._auto_adjust: bool = auto_adjust
        self._cache_dir: Path = cache_dir or YFCACHE
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._result_info: Optional[YFResultInfo] = None

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
                source="yfinance",
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
        end: str = "",
    ) -> YFResultInfo:
        """Download (or reload from cache) OHLCV for *symbols*.

        Returns a ``YFResultInfo`` with provenance metadata.
        """
        syms = symbols or self._symbols
        s = start or self._start
        e = end or self._end

        rows_per_symbol: dict[str, int] = {}
        downloaded_at = datetime.now(timezone.utc).isoformat()

        for sym in syms:
            path = self._cache_dir / f"{sym}.csv"
            if path.exists():
                try:
                    df = pd.read_csv(path, parse_dates=["Date"], index_col="Date")
                    rows_per_symbol[sym] = len(df)
                    continue
                except Exception:
                    pass  # re-download below

            df = self._download_one(sym, s, e)
            if df.empty:
                rows_per_symbol[sym] = 0
                continue
            self._persist(sym, df)
            rows_per_symbol[sym] = len(df)

        res = YFResultInfo(
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

    def _download_one(self, symbol: str, start: str, end: str) -> "pd.DataFrame":
        """One-symbol download, normalised to the standard OHLCV schema."""
        try:
            import yfinance as yf
        except ImportError as e:
            raise RuntimeError(
                "yfinance is required for YFinanceProvider: pip install yfinance"
            ) from e

        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start, end=end, auto_adjust=self._auto_adjust)

        if hist.empty:
            return pd.DataFrame()

        df = hist

        out = pd.DataFrame(index=df.index)
        out.index.name = "Date"

        def _get(col: str) -> pd.Series:
            for candidate in (col, col.capitalize(), col.upper()):
                if candidate in df.columns:
                    s = df[candidate]
                    if isinstance(s, pd.DataFrame):
                        s = s.iloc[:, 0]
                    return s.astype(float)
            return pd.Series(dtype=float, index=df.index)  # pragma: no cover

        out["open"] = _get("Open")
        out["high"] = _get("High")
        out["low"] = _get("Low")
        out["close"] = _get("Close")
        out["volume"] = _get("Volume")

        out = out[out["close"].notna()]
        return out

    def _persist(self, symbol: str, df: pd.DataFrame) -> None:
        """Write *df* to cache as CSV; normalise to tz-naive UTC so that
        reloaded data is always comparable regardless of the source TZ."""
        out = df.copy()
        if out.index.tz is not None:
            out.index = out.index.tz_convert("UTC").tz_localize(None)
        path = self._cache_dir / f"{symbol}.csv"
        out.to_csv(path, date_format="%Y-%m-%d %H:%M:%S")
