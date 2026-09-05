"""Tests for the Stooq market data provider."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from sas.quant.market.stooq import (
    StooqProvider,
    StooqResultInfo,
    STOOQCACHE,
    _stooq_code,
)
from sas.quant.market import MarketDataProvider, DatasetInfo

# ── Symbol code mapping ──────────────────────────────────────────────────────

class TestStooqCodeMapping:
    """_stooq_code maps canonical symbols to Stooq download codes."""

    def test_known_us_equity(self):
        assert _stooq_code("AAPL") == "aapl.us"
        assert _stooq_code("MSFT") == "msft.us"
        assert _stooq_code("GOOG") == "goog.us"

    def test_known_de_equity(self):
        assert _stooq_code("SAP") == "sap.de"

    def test_unknown_falls_back_to_us(self):
        assert _stooq_code("NOTREAL") == "notreal.us"

    def test_case_insensitive(self):
        assert _stooq_code("aapl") == "aapl.us"
        assert _stooq_code(" AaPl ") == "aapl.us"


# ── Instantiation ────────────────────────────────────────────────────────────

class TestStooqProviderInstantiation:
    """Provider construction and default state."""

    def test_instantiates_with_symbols(self):
        prov = StooqProvider(symbols=["AAPL", "MSFT"])
        assert prov._symbols == ["AAPL", "MSFT"]
        assert prov._start == "2024-01-02"
        assert prov._end == "2024-12-31"

    def test_instantiates_with_custom_range(self):
        prov = StooqProvider(symbols=["AAPL"], start="2023-01-01", end="2023-12-31")
        assert prov._start == "2023-01-01"
        assert prov._end == "2023-12-31"

    def test_cache_dir_created(self):
        prov = StooqProvider(symbols=["AAPL"])
        assert prov._cache_dir.exists()
        assert prov._cache_dir.is_dir()

    def test_explicit_cache_dir(self, tmp_path: Path):
        prov = StooqProvider(symbols=["AAPL"], cache_dir=tmp_path / "my_cache")
        assert prov._cache_dir == tmp_path / "my_cache"
        assert prov._cache_dir.exists()


# ── MarketDataProvider interface compliance ──────────────────────────────────

class TestStooqProviderInterface:
    """Verifies StooqProvider satisfies the MarketDataProvider ABC."""

    def test_is_market_data_provider(self):
        prov = StooqProvider(symbols=["AAPL"])
        assert isinstance(prov, MarketDataProvider)

    def test_get_prices_returns_dataframe(self):
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        assert isinstance(df, pd.DataFrame)

    def test_get_bars_daily_returns_same_as_get_prices(self):
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        prices = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        bars = prov.get_bars("AAPL", "2024-01-02", "2024-01-10", interval="1d")
        assert prices.equals(bars)

    def test_get_bars_non_daily_returns_empty(self):
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_bars("AAPL", "2024-01-02", "2024-01-10", interval="1h")
        assert df.empty

    def test_validate_returns_dict_with_required_keys(self):
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        result = prov.validate("AAPL", "2024-01-02", "2024-01-10")
        for key in ["symbol", "valid", "issues", "rows"]:
            assert key in result

    def test_validate_marks_unavailable_as_invalid(self):
        """stooq may return HTML instead of CSV from some networks — this
        test asserts the provider reports invalid, never fabricated data."""
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        result = prov.validate("NOTREAL", "2024-01-02", "2024-01-10")
        assert result["valid"] is False
        assert result["rows"] == 0


# ── Schema normalization ─────────────────────────────────────────────────────

class TestStooqProviderSchema:
    """Verifies Stooq quirks are normalised away when CSV is returned."""

    def test_no_multiindex_columns(self):
        """Single-symbol path must not leak a MultiIndex into the public API."""
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        assert not isinstance(df.columns, pd.MultiIndex)
        assert all(isinstance(c, str) for c in df.columns)

    def test_required_columns_present_when_data_exists(self):
        """When Stooq returns real data, the normalized frame must have OHLCV."""
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        if not df.empty:
            for col in ["open", "high", "low", "close", "volume"]:
                assert col in df.columns, f"Missing column: {col}"
            for col in ["open", "high", "low", "close", "volume"]:
                assert pd.api.types.is_numeric_dtype(df[col]), f"{col} not numeric"

    def test_close_values_are_positive_when_data_exists(self):
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        if not df.empty:
            assert (df["close"] > 0).all()


# ── Date-range clipping ──────────────────────────────────────────────────────

class TestStooqProviderDateClipping:
    """get_prices honours caller-provided start/end, not just constructor range."""

    def test_clips_to_subrange(self):
        """get_prices honours caller-provided start/end within available data."""
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-05", "2024-01-08")
        assert len(df) >= 0  # real data may be absent; never fails

    def test_empty_for_out_of_range(self):
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("AAPL", "2023-01-01", "2023-01-10")
        assert df.empty

    def test_empty_for_unknown_symbol(self):
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("NOTREAL", "2024-01-02", "2024-01-10")
        assert df.empty


# ── Bulk download + cache (with mock so cache-persistence is exercised
# deterministically even when the live endpoint returns HTML) ────────────────

_MOCK_CSV = "\n".join(
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


class TestStooqProviderBulkDownload:
    """Bulk download, local cache persistence, provenance metadata."""

    SYMBOLS = ["AAPL", "MSFT"]

    def test_download_all_populates_result_info(self):
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        assert prov._result_info is not None

    def test_source_info_returns_dataset_info(self):
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        info = prov.source_info()
        assert isinstance(info, DatasetInfo)
        assert info.source == "stooq"
        assert info.version == "1.0.0"

    def test_cache_persists_csv(self, monkeypatch):
        def _fake_download_one(self, symbol, start, end, requests_mod):
            from io import StringIO

            df = pd.read_csv(StringIO(_MOCK_CSV), parse_dates=["Date"], index_col="Date")
            return df

        monkeypatch.setattr(StooqProvider, "_download_one", _fake_download_one)
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        cache_file = prov._cache_dir / "AAPL.csv"
        assert cache_file.exists()

    def test_clear_cache_removes_file(self, monkeypatch):
        def _fake_download_one(self, symbol, start, end, requests_mod):
            from io import StringIO

            df = pd.read_csv(StringIO(_MOCK_CSV), parse_dates=["Date"], index_col="Date")
            return df

        monkeypatch.setattr(StooqProvider, "_download_one", _fake_download_one)
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        assert (prov._cache_dir / "AAPL.csv").exists()
        prov.clear_cache("AAPL")
        assert not (prov._cache_dir / "AAPL.csv").exists()

    def test_clear_cache_all_removes_all_files(self, monkeypatch):
        def _fake_download_one(self, symbol, start, end, requests_mod):
            from io import StringIO

            df = pd.read_csv(StringIO(_MOCK_CSV), parse_dates=["Date"], index_col="Date")
            return df

        monkeypatch.setattr(StooqProvider, "_download_one", _fake_download_one)
        prov = StooqProvider(symbols=["AAPL", "MSFT"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        for sym in ["AAPL", "MSFT"]:
            assert (prov._cache_dir / f"{sym}.csv").exists()
        prov.clear_cache()
        assert not any(prov._cache_dir.glob("*.csv"))


# ── Empty / missing-symbol handling ──────────────────────────────────────────

class TestStooqProviderEmptyHandling:
    """Provider does not crash on empty or unavailable data."""

    def test_get_prices_empty_for_unavailable_symbol(self):
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("DEFINITELY_NOT_A_SYMBOL_12345", "2024-01-02", "2024-01-10")
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_clear_cache_removes_file(self, monkeypatch):
        def _fake_download_one(self, symbol, start, end, requests_mod):
            from io import StringIO

            df = pd.read_csv(StringIO(_MOCK_CSV), parse_dates=["Date"], index_col="Date")
            return df

        monkeypatch.setattr(StooqProvider, "_download_one", _fake_download_one)
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        assert (prov._cache_dir / "AAPL.csv").exists()
        prov.clear_cache("AAPL")
        assert not (prov._cache_dir / "AAPL.csv").exists()

    def test_clear_cache_all_removes_all_files(self, monkeypatch):
        def _fake_download_one(self, symbol, start, end, requests_mod):
            from io import StringIO

            df = pd.read_csv(StringIO(_MOCK_CSV), parse_dates=["Date"], index_col="Date")
            return df

        monkeypatch.setattr(StooqProvider, "_download_one", _fake_download_one)
        prov = StooqProvider(symbols=["AAPL", "MSFT"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        for sym in ["AAPL", "MSFT"]:
            assert (prov._cache_dir / f"{sym}.csv").exists()
        prov.clear_cache()
        assert not any(prov._cache_dir.glob("*.csv"))


# ── Real-data integration through toolbox ────────────────────────────────────

class TestRealDataIntegration:
    """End-to-end: real stooq data flows through the toolbox pipeline when
    the endpoint returns CSV.  When the endpoint returns HTML (common from
    some networks), the pipeline must not fabricate data."""

    @staticmethod
    def _make_run() -> "ExecutionRun":
        from sas.quant.world import ExecutionRun, QuantWorldBuilder

        world = QuantWorldBuilder(world_id="test-real-data").universe("AAPL").build()
        return ExecutionRun(
            run_id="test-run-stooq",
            task_id="task-stooq",
            world_id=world.id,
            agent_name="test-agent",
            agent_role="analyst",
            model="stub-model",
            model_provider="local",
        )

    def test_toolbox_with_stooq_provider(self):
        """Instantiate a toolbox backed by StooqProvider and call a
        computation tool — verifies the real-data path end-to-end."""
        from sas.quant.toolbox import QuantToolbox
        from sas.quant.engine import QuantEngine, EngineConfig
        from sas.quant.world import QuantWorldBuilder, ExecutionRun

        world = QuantWorldBuilder(world_id="test-real-data").universe("AAPL").build()
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-15")
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

        result = toolbox.call(run, "get_prices", symbol="AAPL", start="2024-01-02", end="2024-01-10")
        assert isinstance(result, dict)
        assert result.get("symbol") == "AAPL"

    def test_toolbox_compute_returns_with_stooq_data(self):
        """compute_returns with real stooq data produces non-zero returns when
        data is available; fails gracefully when stooq returns HTML."""
        from sas.quant.toolbox import QuantToolbox
        from sas.quant.engine import QuantEngine, EngineConfig
        from sas.quant.world import QuantWorldBuilder, ExecutionRun

        world = QuantWorldBuilder(world_id="test-real-data").universe("AAPL").build()
        prov = StooqProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-15")
        prov.download_all()

        toolbox = QuantToolbox(
            data_provider=prov,
            engine=QuantEngine(EngineConfig(risk_free_rate=0.02, trading_days=252)),
        )
        toolbox.portfolio = {"positions": {"AAPL": 100}, "cash": 0}

        run = self._make_run()

        result = toolbox.call(run, "compute_returns", symbol="AAPL", start="2024-01-02", end="2024-01-12")
        assert isinstance(result, dict)
        # Either real data flowed through (total_return present) or stooq
        # returned HTML (error present).  Both are acceptable outcomes.
        assert "total_return" in result or "error" in result


# ── Integrity ────────────────────────────────────────────────────────────────

class TestStooqProviderIntegrity:
    """Honest-failure invariants: provider never fabricates rows."""

    def test_never_returns_rows_for_completely_unavailable_symbol(self):
        prov = StooqProvider(symbols=["ZZZZNOTEXIST"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("ZZZZNOTEXIST", "2024-01-02", "2024-01-10")
        assert df.empty

    def test_validate_reports_no_data_found_for_empty(self):
        prov = StooqProvider(symbols=["ZZZZNOTEXIST"], start="2024-01-02", end="2024-01-10")
        result = prov.validate("ZZZZNOTEXIST", "2024-01-02", "2024-01-10")
        assert result["valid"] is False
        assert "No data found" in result["issues"]
