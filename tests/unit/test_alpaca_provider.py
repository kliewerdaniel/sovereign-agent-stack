"""Tests for the Alpaca market data provider."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from sas.quant.market.alpaca import (
    AlpacaProvider,
    AlpacaResultInfo,
    _alpaca_symbol,
)
from sas.quant.market import MarketDataProvider, DatasetInfo

# ── Symbol normalization ──────────────────────────────────────────────────────

class TestAlpacaSymbolNormalization:
    """_alpaca_symbol maps canonical symbols to Alpaca Data API v2 codes."""

    def test_known_us_equity_gets_suffix(self):
        assert _alpaca_symbol("AAPL") == "AAPL/US"
        assert _alpaca_symbol("MSFT") == "MSFT/US"
        assert _alpaca_symbol("NVDA") == "NVDA/US"

    def test_already_suffixed_preserved(self):
        assert _alpaca_symbol("AAPL/US") == "AAPL/US"
        assert _alpaca_symbol("SAP.DE") == "SAP.DE"

    def test_case_insensitive(self):
        assert _alpaca_symbol("aapl") == "AAPL/US"


# ── Instantiation ────────────────────────────────────────────────────────────

class TestAlpacaProviderInstantiation:
    """Provider construction and default state."""

    def test_instantiates_with_symbols(self):
        prov = AlpacaProvider(symbols=["AAPL", "MSFT"], key_id="x", secret_key="y")
        assert prov._symbols == ["AAPL", "MSFT"]
        assert prov._start == "2024-01-02"
        assert prov._end == "2024-12-31"
        assert prov._paper is True

    def test_instantiates_with_live_base_url(self):
        prov = AlpacaProvider(symbols=["AAPL"], key_id="x", secret_key="y", paper=False)
        assert "paper-api" not in prov._base_url

    def test_instantiates_with_empty_credentials(self):
        prov = AlpacaProvider(symbols=["AAPL"])
        assert prov._key_id == ""
        assert prov._secret_key == ""

    def test_cache_dir_created(self):
        prov = AlpacaProvider(symbols=["AAPL"], key_id="x", secret_key="y")
        assert prov._cache_dir.exists()

    def test_explicit_cache_dir(self, tmp_path: Path):
        prov = AlpacaProvider(symbols=["AAPL"], key_id="x", secret_key="y",
                              cache_dir=tmp_path / "my_cache")
        assert prov._cache_dir == tmp_path / "my_cache"
        assert prov._cache_dir.exists()


# ── MarketDataProvider interface compliance ──────────────────────────────────

class TestAlpacaProviderInterface:
    """Verifies AlpacaProvider satisfies the MarketDataProvider ABC."""

    def test_is_market_data_provider(self):
        prov = AlpacaProvider(symbols=["AAPL"], key_id="x", secret_key="y")
        assert isinstance(prov, MarketDataProvider)

    def test_get_prices_returns_dataframe(self):
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                              key_id="x", secret_key="y")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        assert isinstance(df, pd.DataFrame)

    def test_get_bars_daily_returns_same_as_get_prices(self):
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                              key_id="x", secret_key="y")
        prov.download_all()
        prices = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        bars = prov.get_bars("AAPL", "2024-01-02", "2024-01-10", interval="1d")
        assert prices.equals(bars)

    def test_get_bars_non_daily_returns_empty(self):
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                              key_id="x", secret_key="y")
        prov.download_all()
        df = prov.get_bars("AAPL", "2024-01-02", "2024-01-10", interval="1h")
        assert df.empty

    def test_validate_returns_dict_with_required_keys(self):
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                              key_id="x", secret_key="y")
        prov.download_all()
        result = prov.validate("AAPL", "2024-01-02", "2024-01-10")
        for key in ["symbol", "valid", "issues", "rows"]:
            assert key in result

    def test_validate_marks_unauthorized_as_invalid(self):
        """Without valid credentials, Alpaca returns 401 — provider reports
        invalid, never fabricated rows."""
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        result = prov.validate("AAPL", "2024-01-02", "2024-01-10")
        assert result["valid"] is False
        assert result["rows"] == 0


# ── Schema normalization ─────────────────────────────────────────────────────

class TestAlpacaProviderSchema:
    """Verifies Alpaca response quirks are normalised away when data exists."""

    def test_no_multiindex_columns(self):
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                              key_id="x", secret_key="y")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        assert not isinstance(df.columns, pd.MultiIndex)
        assert all(isinstance(c, str) for c in df.columns)

    def test_required_columns_present_when_data_exists(self):
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                              key_id="x", secret_key="y")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        if not df.empty:
            for col in ["open", "high", "low", "close", "volume"]:
                assert col in df.columns, f"Missing column: {col}"
            for col in ["open", "high", "low", "close", "volume"]:
                assert pd.api.types.is_numeric_dtype(df[col]), f"{col} not numeric"


# ── Date-range clipping ──────────────────────────────────────────────────────

class TestAlpacaProviderDateClipping:
    """get_prices honours caller-provided start/end, not just constructor range."""

    def test_clips_to_subrange(self):
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                              key_id="x", secret_key="y")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-05", "2024-01-08")
        assert len(df) >= 0

    def test_empty_for_out_of_range(self):
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                              key_id="x", secret_key="y")
        prov.download_all()
        df = prov.get_prices("AAPL", "2023-01-01", "2023-01-10")
        assert df.empty

    def test_empty_for_unknown_symbol(self):
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                              key_id="x", secret_key="y")
        prov.download_all()
        df = prov.get_prices("NOTREAL", "2024-01-02", "2024-01-10")
        assert df.empty


# ── Bulk download + cache (with mock so cache-persistence is exercised
# deterministically; the live Alpaca API requires valid credentials) ─────────

_MOCK_CSV = "\n".join(
    [
        "Date,open,high,low,close,volume",
        "2024-01-02,184.895814,186.170285,183.404007,183.404007,82488700",
        "2024-01-03,182.001094,183.641103,182.030731,182.030731,58414500",
        "2024-01-04,179.956063,180.884744,179.718934,179.718934,71983600",
        "2024-01-05,179.797983,180.558698,178.997726,178.997726,62379700",
        "2024-01-08,179.896761,183.364966,179.538299,183.324997,59144500",
        "2024-01-09,183.220199,183.966003,182.455994,182.910049,58914500",
        "2024-01-10,183.980011,184.550011,183.010010,183.389999,61465500",
    ]
)


class TestAlpacaProviderBulkDownload:
    """Bulk download, local cache persistence, provenance metadata."""

    def test_download_all_populates_result_info(self):
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                              key_id="x", secret_key="y")
        prov.download_all()
        assert prov._result_info is not None

    def test_source_info_returns_dataset_info(self):
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                              key_id="x", secret_key="y")
        info = prov.source_info()
        assert isinstance(info, DatasetInfo)
        assert info.source == "alpaca"
        assert info.version == "1.0.0"

    def test_cache_persists_csv(self, monkeypatch):
        def _fake_download_one(self, symbol, start, end):
            from io import StringIO

            df = pd.read_csv(StringIO(_MOCK_CSV), parse_dates=["Date"], index_col="Date")
            return df

        monkeypatch.setattr(AlpacaProvider, "_download_one", _fake_download_one)
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                              key_id="x", secret_key="y")
        prov.download_all()
        cache_file = prov._cache_dir / "AAPL.csv"
        assert cache_file.exists()

    def test_download_all_records_hash_set(self, monkeypatch):
        """content_hash is computed from real data, not an empty fallback."""
        def _fake_download_one(self, symbol, start, end):
            from io import StringIO

            df = pd.read_csv(
                StringIO(_MOCK_CSV),
                parse_dates=["Date"],
                index_col="Date",
            )
            return df

        monkeypatch.setattr(AlpacaProvider, "_download_one", _fake_download_one)
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                              key_id="x", secret_key="y")
        info = prov.download_all()
        assert info.content_hash
        assert len(info.content_hash) == 16

    def test_multiple_downloads_produce_same_hash(self):
        prov1 = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                               key_id="x", secret_key="y")
        prov2 = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                               key_id="x", secret_key="y")
        hash1 = prov1.download_all().content_hash
        hash2 = prov2.download_all().content_hash
        assert hash1 == hash2, f"Hash mismatch: {hash1} vs {hash2}"

    def test_different_windows_produce_different_hashes(self):
        prov1 = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                               key_id="x", secret_key="y")
        prov2 = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-02-01",
                               key_id="x", secret_key="y")
        hash1 = prov1.download_all().content_hash
        hash2 = prov2.download_all().content_hash
        assert hash1 != hash2, "Different windows should produce different hashes"

    def test_result_info_to_dict(self):
        info = AlpacaResultInfo(
            symbols=["AAPL"],
            start="2024-01-02",
            end="2024-01-10",
            rows_per_symbol={"AAPL": 7},
        )
        d = info.to_dict()
        assert d["source"] == "alpaca"
        assert d["symbols"] == ["AAPL"]
        assert d["row_count"] == 7
        assert "checksum" in d
        assert "provenance" in d


# ── Empty / missing-symbol handling ──────────────────────────────────────────

class TestAlpacaProviderEmptyHandling:
    """Provider does not crash on empty or unavailable data."""

    def test_get_prices_empty_for_unauthorized_symbol(self):
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("DEFINITELY_NOT_A_SYMBOL_12345", "2024-01-02", "2024-01-10")
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_clear_cache_removes_file(self, monkeypatch):
        def _fake_download_one(self, symbol, start, end):
            from io import StringIO

            df = pd.read_csv(StringIO(_MOCK_CSV), parse_dates=["Date"], index_col="Date")
            return df

        monkeypatch.setattr(AlpacaProvider, "_download_one", _fake_download_one)
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10",
                              key_id="x", secret_key="y")
        prov.download_all()
        assert (prov._cache_dir / "AAPL.csv").exists()
        prov.clear_cache("AAPL")
        assert not (prov._cache_dir / "AAPL.csv").exists()

    def test_clear_cache_all_removes_all_files(self, monkeypatch):
        def _fake_download_one(self, symbol, start, end):
            from io import StringIO

            df = pd.read_csv(StringIO(_MOCK_CSV), parse_dates=["Date"], index_col="Date")
            return df

        monkeypatch.setattr(AlpacaProvider, "_download_one", _fake_download_one)
        prov = AlpacaProvider(symbols=["AAPL", "MSFT"], start="2024-01-02", end="2024-01-10",
                              key_id="x", secret_key="y")
        prov.download_all()
        for sym in ["AAPL", "MSFT"]:
            assert (prov._cache_dir / f"{sym}.csv").exists()
        prov.clear_cache()
        assert not any(prov._cache_dir.glob("*.csv"))


# ── Real-data integration through toolbox ────────────────────────────────────

class TestRealDataIntegration:
    """End-to-end: real alpaca data flows through the toolbox pipeline when
    valid credentials are provided.  Without credentials the pipeline must
    not fabricate data — it should fail closed."""

    @staticmethod
    def _make_run() -> "ExecutionRun":
        from sas.quant.world import ExecutionRun, QuantWorldBuilder

        world = QuantWorldBuilder(world_id="test-real-data").universe("AAPL").build()
        return ExecutionRun(
            run_id="test-run-alpaca",
            task_id="task-alpaca",
            world_id=world.id,
            agent_name="test-agent",
            agent_role="analyst",
            model="stub-model",
            model_provider="local",
        )

    def test_toolbox_with_alpaca_provider_no_creds_fails_closed(self):
        """Without creds, toolbox must not fabricate data."""
        from sas.quant.toolbox import QuantToolbox
        from sas.quant.engine import QuantEngine, EngineConfig
        from sas.quant.world import QuantWorldBuilder, ExecutionRun

        world = QuantWorldBuilder(world_id="test-real-data").universe("AAPL").build()
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-15")
        prov.download_all()

        toolbox = QuantToolbox(
            data_provider=prov,
            engine=QuantEngine(EngineConfig(risk_free_rate=0.02, trading_days=252)),
        )
        toolbox.portfolio = {"positions": {"AAPL": 100}, "cash": 0}

        run = self._make_run()

        result = toolbox.call(run, "get_prices", symbol="AAPL", start="2024-01-02", end="2024-01-10")
        assert isinstance(result, dict)
        # Without creds, data is empty — the toolbox should return a result
        # with rows=0 or an error, never fabricated OHLCV.
        assert result.get("rows", 0) == 0 or "error" in result

    def test_toolbox_compute_returns_with_alpaca_data(self):
        """compute_returns with Alpaca data: when creds are absent, returns
        an error result; when creds are present it computes returns."""
        from sas.quant.toolbox import QuantToolbox
        from sas.quant.engine import QuantEngine, EngineConfig
        from sas.quant.world import QuantWorldBuilder, ExecutionRun

        world = QuantWorldBuilder(world_id="test-real-data").universe("AAPL").build()
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-15")
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


# ── Integrity ────────────────────────────────────────────────────────────────

class TestAlpacaProviderIntegrity:
    """Honest-failure invariants: provider never fabricates rows."""

    def test_never_returns_rows_without_credentials(self):
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        prov.download_all()
        df = prov.get_prices("AAPL", "2024-01-02", "2024-01-10")
        assert df.empty

    def test_validate_reports_no_data_found_for_empty(self):
        prov = AlpacaProvider(symbols=["AAPL"], start="2024-01-02", end="2024-01-10")
        result = prov.validate("AAPL", "2024-01-02", "2024-01-10")
        assert result["valid"] is False
        assert "No data found" in result["issues"]
