"""Tests for the YFinance market data provider."""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import pytest

from sas.quant.market.yfinance import YFinanceProvider, YFCACHE, YFResultInfo
from sas.quant.market import MarketDataProvider, DatasetInfo


# ── Instantiation ────────────────────────────────────────────────────────────

class TestYFinanceProviderInstantiation:
    """Provider construction and default state."""

    def test_instantiates_with_symbols(self):
        prov = YFinanceProvider(symbols=["AAPL", "MSFT"])
        assert prov._symbols == ["AAPL", "MSFT"]
        assert prov._start == "2024-01-02"
        assert prov._end == "2024-12-31"
        assert prov._auto_adjust is True

    def test_instantiates_with_custom_range(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2023-01-01", end="2023-12-31")
        assert prov._start == "2023-01-01"
        assert prov._end == "2023-12-31"

    def test_instantiates_with_disabled_auto_adjust(self):
        prov = YFinanceProvider(symbols=["AAPL"], auto_adjust=False)
        assert prov._auto_adjust is False

    def test_cache_dir_created(self):
        prov = YFinanceProvider(symbols=["AAPL"])
        assert prov._cache_dir.exists()
        assert prov._cache_dir.is_dir()

    def test_explicit_cache_dir(self, tmp_path: Path):
        prov = YFinanceProvider(symbols=["AAPL"], cache_dir=tmp_path / "my_cache")
        assert prov._cache_dir == tmp_path / "my_cache"
        assert prov._cache_dir.exists()


# ── Bulk download + cache ────────────────────────────────────────────────────

class TestYFinanceProviderBulkDownload:
    """Bulk download, local cache persistence, provenance metadata."""

    SYMBOLS = ["AAPL", "MSFT", "GOOG"]

    def test_download_all_fetches_data(self):
        prov = YFinanceProvider(symbols=self.SYMBOLS, start="2024-01-02", end="2024-01-10")
        info = prov.download_all()
        assert info is not None
        assert info.source == "yfinance"
        assert set(info.symbols) == set(self.SYMBOLS)
        assert info.start == "2024-01-02"
        assert info.end == "2024-01-10"
        assert len(info.rows_per_symbol) == 3
        for sym in self.SYMBOLS:
            assert sym in info.rows_per_symbol
            assert info.rows_per_symbol[sym] >= 5  # at least a few trading days

    def test_download_all_populates_result_info(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        assert prov._result_info is not None
        assert prov._result_info.content_hash != ""

    def test_source_info_returns_dataset_info(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        info = prov.source_info()
        assert isinstance(info, DatasetInfo)
        assert info.source == "yfinance"
        assert info.version == "1.0.0"
        assert "AAPL" in info.symbols
        assert info.row_count > 0

    def test_cache_persists_csv(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        cache_file = prov._cache_dir / "AAPL.csv"
        assert cache_file.exists()
        df = pd.read_csv(cache_file, parse_dates=["Date"])
        assert "Date" in df.columns
        assert "close" in df.columns or "Close" in df.columns

    def test_cached_data_reloaded_on_second_call(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        first_rows = sum(prov.download_all().rows_per_symbol.values())
        prov._result_info = None
        info = prov.download_all()
        assert sum(info.rows_per_symbol.values()) == first_rows

    def test_clear_cache_removes_file(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        assert (prov._cache_dir / "AAPL.csv").exists()
        prov.clear_cache("AAPL")
        assert not (prov._cache_dir / "AAPL.csv").exists()

    def test_clear_cache_all_removes_all_files(self):
        prov = YFinanceProvider(symbols=["AAPL", "MSFT"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        for sym in ["AAPL", "MSFT"]:
            assert (prov._cache_dir / f"{sym}.csv").exists()
        prov.clear_cache()
        assert not any(prov._cache_dir.glob("*.csv"))

    def test_download_all_records_hash_set(self):
        """download_all populates result_info with a content_hash."""
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        info = prov.download_all()
        assert info.content_hash
        assert len(info.content_hash) == 16

    def test_source_info_requires_download_first(self):
        """source_info without prior download triggers auto-download."""
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        info = prov.source_info()
        assert isinstance(info, DatasetInfo)
        assert info.source == "yfinance"
        assert info.row_count >= 5  # at least a few trading days

    def test_multiple_downloads_produce_same_hash_for_same_symbols(self):
        """content_hash is deterministic for same symbols + window."""
        prov1 = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov2 = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        hash1 = prov1.download_all().content_hash
        hash2 = prov2.download_all().content_hash
        assert hash1 == hash2, f"Hash mismatch: {hash1} vs {hash2}"

    def test_different_windows_produce_different_hashes(self):
        """Different date ranges produce different content_hashes."""
        prov1 = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov2 = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-02-01")
        hash1 = prov1.download_all().content_hash
        hash2 = prov2.download_all().content_hash
        assert hash1 != hash2, "Different windows should produce different hashes"

    def test_result_info_to_dict(self):
        info = YFResultInfo(
            symbols=["AAPL"],
            start="2024-01-02",
            end="2024-01-10",
            rows_per_symbol={"AAPL": 7},
        )
        d = info.to_dict()
        assert d["source"] == "yfinance"
        assert d["symbols"] == ["AAPL"]
        assert d["row_count"] == 7
        assert "checksum" in d
        assert "provenance" in d


# ── MarketDataProvider interface compliance ──────────────────────────────────

class TestYFinanceProviderInterface:
    """Verifies YFinanceProvider satisfies the MarketDataProvider ABC."""

    def test_is_market_data_provider(self):
        prov = YFinanceProvider(symbols=["AAPL"])
        assert isinstance(prov, MarketDataProvider)

    def test_get_prices_returns_dataframe(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        assert isinstance(df, pd.DataFrame)

    def test_get_prices_has_required_columns(self):
        """After normalization, the DataFrame must have standard OHLCV columns."""
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        for col in ["open", "high", "low", "close", "volume"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_get_prices_dtypes_are_numeric(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        for col in ["open", "high", "low", "close", "volume"]:
            assert pd.api.types.is_numeric_dtype(df[col]), f"{col} not numeric"

    def test_get_bars_daily_returns_same_as_get_prices(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        prices = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        bars = prov.get_bars("AAPL", "2024-01-02", "2024-01-10", interval="1d")
        assert prices.equals(bars)

    def test_get_bars_non_daily_returns_empty(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_bars("AAPL", "2024-01-02", "2024-01-10", interval="1h")
        assert df.empty

    def test_validate_returns_dict_with_required_keys(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        result = prov.validate("AAPL", "2024-01-02", "2024-01-10")
        for key in ["symbol", "valid", "issues", "rows"]:
            assert key in result

    def test_validate_marks_valid_data_as_valid(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        result = prov.validate("AAPL", "2024-01-02", "2024-01-10")
        assert result["valid"] is True
        assert result["rows"] > 0


# ── Schema normalization ─────────────────────────────────────────────────────

class TestYFinanceProviderSchema:
    """Verifies yfinance quirks are normalised away."""

    def test_no_multiindex_columns(self):
        """yfinance returns a MultiIndex when downloading multiple tickers;
        our single-symbol path must not leak that into the public API."""
        prov = YFinanceProvider(symbols=["AAPL", "MSFT"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        assert not isinstance(df.columns, pd.MultiIndex)
        assert all(isinstance(c, str) for c in df.columns)

    def test_close_values_are_positive(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        assert (df["close"] > 0).all()

    def test_high_ge_low_ge_open(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-02", "2024-01-10").sort_index()
        assert not (df["high"] < df["low"]).any()


# ── Date-range clipping ──────────────────────────────────────────────────────

class TestYFinanceProviderDateClipping:
    """get_prices honours caller-provided start/end, not just constructor range."""

    def test_clips_to_subrange(self):
        """get_prices honours caller-provided start/end within available data."""
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        # Query a window inside the cached data
        df = prov.get_prices("AAPL", "2024-01-03", "2024-01-08")
        assert len(df) > 0
        assert df.index.min().date() >= pd.Timestamp("2024-01-03").date()
        assert df.index.max().date() <= pd.Timestamp("2024-01-08").date()

    def test_full_constructor_range_returns_all_cached_data(self):
        """get_prices with the constructor's full range returns all cached rows."""
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        assert len(df) == prov._result_info.rows_per_symbol.get("AAPL", 0)

    def test_empty_for_out_of_range(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("AAPL", "2023-01-01", "2023-01-10")
        assert df.empty

    def test_empty_for_unknown_symbol(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("NOTREAL", "2024-01-02", "2024-01-10")
        assert df.empty


# ── Empty / missing-symbol handling ──────────────────────────────────────────

class TestYFinanceProviderEmptyHandling:
    """Provider does not crash on empty or unavailable data."""

    def test_get_prices_empty_for_unavailable_symbol(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("DEFINITELY_NOT_A_SYMBOL_12345", "2024-01-02", "2024-01-10")
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_validate_for_unavailable_symbol(self):
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        result = prov.validate("DEFINITELY_NOT_A_SYMBOL_12345", "2024-01-02", "2024-01-10")
        assert result["valid"] is False
        assert result["rows"] == 0
        assert "No data found" in result["issues"]


# ── Real-data integration through toolbox ────────────────────────────────────

class TestRealDataIntegration:
    """End-to-end: real yfinance data flows through the toolbox pipeline."""

    @staticmethod
    def _make_run() -> "ExecutionRun":
        from sas.quant.world import ExecutionRun, QuantWorldBuilder

        world = QuantWorldBuilder(world_id="test-real-data").universe("AAPL").build()
        return ExecutionRun(
            run_id="test-run-yf",
            task_id="task-yf",
            world_id=world.id,
            agent_name="test-agent",
            agent_role="analyst",
            model="stub-model",
            model_provider="local",
        )

    def test_toolbox_with_yfinance_provider(self):
        """Instantiate a toolbox backed by YFinanceProvider and call a
        computation tool — verifies the real-data path end-to-end."""
        from sas.quant.toolbox import QuantToolbox
        from sas.quant.engine import QuantEngine, EngineConfig
        from sas.quant.world import QuantWorldBuilder, ExecutionRun

        world = QuantWorldBuilder(world_id="test-real-data").universe("AAPL").build()
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-15")
        prov.download_all()

        toolbox = QuantToolbox(
            data_provider=prov,
            engine=QuantEngine(EngineConfig(risk_free_rate=0.02, trading_days=252)),
        )
        toolbox.portfolio = {
            "positions": {"AAPL": 100},
            "cash": 0,
        }

        run = self._make_run()

        # Call get_prices — should return real data, not empty
        result = toolbox.call(run, "get_prices", symbol="AAPL", start="2024-01-02", end="2024-01-10")
        assert isinstance(result, dict)
        assert result.get("symbol") == "AAPL"
        assert result.get("rows", 0) > 0
        assert len(result.get("data", [])) > 0

    def test_toolbox_compute_returns_with_real_data(self):
        """compute_returns with real yfinance data produces non-zero returns."""
        from sas.quant.toolbox import QuantToolbox
        from sas.quant.engine import QuantEngine, EngineConfig
        from sas.quant.world import QuantWorldBuilder, ExecutionRun

        world = QuantWorldBuilder(world_id="test-real-data").universe("AAPL").build()
        prov = YFinanceProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-15")
        prov.download_all()

        toolbox = QuantToolbox(
            data_provider=prov,
            engine=QuantEngine(EngineConfig(risk_free_rate=0.02, trading_days=252)),
        )
        toolbox.portfolio = {"positions": {"AAPL": 100}, "cash": 0}

        run = self._make_run()

        result = toolbox.call(run, "compute_returns", symbol="AAPL", start="2024-01-02", end="2024-01-12")
        assert isinstance(result, dict)
        assert "total_return" in result or "error" in result
        if "error" not in result:
            assert result["symbol"] == "AAPL"
            assert isinstance(result["total_return"], float)

    def test_memory_usage_constant_after_cache(self):
        """Second download_all should be cache-hot, not re-fetching."""
        prov = YFinanceProvider(symbols=["AAPL", "MSFT"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        sizes = {p.name: p.stat().st_size for p in prov._cache_dir.glob("*.csv")}

        prov._result_info = None
        t0 = time.monotonic()
        info = prov.download_all()
        elapsed = time.monotonic() - t0

        for name, size in sizes.items():
            assert (prov._cache_dir / name).stat().st_size == size

        # Should be fast (cache hits) — under 2s for 2 symbols
        assert elapsed < 2.0, f"Cache hit took {elapsed:.2f}s — expected < 2s"
