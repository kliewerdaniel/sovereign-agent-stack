"""
Stooq market data provider for Sovereign Quant.

Free CSV download endpoint: https://stooq.com/q/d/l/?s={symbol}&d1={yyyyMMdd}&d2={yyyyMMdd}&i=d

No API key required.  Treat all external data as untrusted — always call
``validate()`` before use.

IMPORTANT: Stooq's free CSV endpoint has intermittently returned non-CSV
responses (HTML) from some networks/IPs.  When that happens the provider
returns an empty DataFrame and ``validate`` reports ``"No data found"`` —
never fabricated rows.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from sas.quant.market import MarketDataProvider, MarketDataPoint, DatasetInfo

STOOQCACHE = Path.home() / ".sas" / "stooq_cache"
STOOQCACHE.mkdir(parents=True, exist_ok=True)

# Explicit exchange-suffix map for symbols whose ticker is ambiguous.
# Stooq uses exchange-suffixed codes (aapl.us, sap.de, vow3.de, etc.).
STOOQ_CODE_MAP: dict[str, str] = {
    "AAPL": "aapl.us",
    "MSFT": "msft.us",
    "GOOG": "goog.us",
    "AMZN": "amzn.us",
    "NVDA": "nvda.us",
    "META": "meta.us",
    "SPY": "spy.us",
    "QQQ": "qqq.us",
    "IWM": "iwm.us",
    "TLT": "tlt.us",
    "SAP": "sap.de",
    "VOW3": "vow3.de",
    "BMW": "bmw.de",
    "Siemens": "snm.de",
}


def _stooq_code(symbol: str) -> str:
    """Map a canonical symbol to a Stooq download code."""
    s = symbol.upper().strip()
    return STOOQ_CODE_MAP.get(s, f"{s.lower()}.us")


@dataclass
class StooqResultInfo:
    """Metadata returned by a Stooq bulk download for provenance."""

    symbols: list[str]
    start: str
    end: str
    rows_per_symbol: dict[str, int]
    source: str = "stooq"
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


class StooqProvider(MarketDataProvider):
    """Market data provider backed by the free Stooq CSV endpoint.

    Downloads daily OHLCV bars for a list of symbols, caches them locally
    under ``~/.sas/stooq_cache/<symbol>.csv``, and serves them through the
    MarketDataProvider interface.

    IMPORTANT: Stooq data quality varies and the free endpoint has
    intermittently returned HTML instead of CSV from some networks.  The
    provider fails closed — empty frames and honest validation — rather than
    fabricating rows.
    """

    def __init__(
        self,
        symbols: list[str],
        start: str = "2024-01-02",
        end: str = "2024-12-31",
        cache_dir: Optional[Path] = None,
    ):
        self._symbols: list[str] = list(symbols)
        self._start: str = start
        self._end: str = end
        self._cache_dir: Path = cache_dir or STOOQCACHE
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._result_info: Optional[StooqResultInfo] = None

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
                source="stooq",
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
    ) -> StooqResultInfo:
        """Download (or reload from cache) OHLCV for *symbols*.

        Returns a ``StooqResultInfo`` with provenance metadata.  When
        ``_fetch_fresh`` is True, re-downloads even cached symbols (used by
        tests that want to observe a live fetch).
        """
        import requests as _requests

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

            df = self._download_one(sym, s, e, _requests)
            if df.empty:
                rows_per_symbol[sym] = 0
                continue
            self._persist(sym, df)
            rows_per_symbol[sym] = len(df)

        res = StooqResultInfo(
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

    def _download_one(
        self, symbol: str, start: str, end: str, requests_mod
    ) -> "pd.DataFrame":
        """One-symbol download, normalised to the standard OHLCV schema."""
        url = "https://stooq.com/q/d/l/"
        params = {
            "s": _stooq_code(symbol),
            "d1": start.replace("-", ""),
            "d2": end.replace("-", ""),
            "i": "d",
        }
        try:
            r = requests_mod.get(url, params=params, timeout=40,
                                 headers={"User-Agent": "SovereignQuant/1.0"})
        except Exception as e:
            print(f"[stooq] fetch error {symbol}: {type(e).__name__}: {e}")
            return pd.DataFrame()

        if r.status_code != 200:
            print(f"[stooq] non-200 {symbol}: {r.status_code} len={len(r.text)}")
            return pd.DataFrame()

        text = r.text
        if not text or text.lstrip().startswith("<"):
            print(f"[stooq] non-csv {symbol}: len={len(text)} head={text[:80]!r}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(
                pd.io.common.StringIO(text), parse_dates=["Date"], dayfirst=False
            )
        except Exception as e:
            print(f"[stooq] parse error {symbol}: {type(e).__name__}: {e}\n{text[:200]}")
            return pd.DataFrame()

        if df.empty:
            return pd.DataFrame()

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

        out["open"] = _get("Open") if "Open" in df.columns else _get("open")
        out["high"] = _get("High") if "High" in df.columns else _get("high")
        out["low"] = _get("Low") if "Low" in df.columns else _get("low")
        out["close"] = _get("Close") if "Close" in df.columns else _get("close")
        out["volume"] = _get("Volume") if "Volume" in df.columns else _get("volume")

        out = out[out["close"].notna()]
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
        import requests as _requests

        return self._download_one(symbol, self._start, self._end, _requests)

    def _persist(self, symbol: str, df: pd.DataFrame) -> None:
        """Write *df* to cache as CSV; normalise to tz-naive UTC."""
        out = df.copy()
        if out.index.tz is not None:
            out.index = out.index.tz_convert("UTC").tz_localize(None)
        path = self._cache_dir / f"{symbol}.csv"
        out.to_csv(path, date_format="%Y-%m-%d %H:%M:%S")
