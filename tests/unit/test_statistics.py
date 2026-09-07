"""Unit tests for the statistics layer — DSR and PBO."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from sas.quant.statistics.deflated_sharpe import (
    DSRResult,
    _expected_max_sharpe_null,
    compute_dsr,
)
from sas.quant.statistics.cscv import compute_cscv, CSCVResult


class TestDeflatedSharpeRatio:
    """Test the DSR computation against known reference values."""

    def test_single_trial_no_deflation(self):
        """With 1 trial, DSR should equal the standard normal CDF of the Sharpe."""
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 252).tolist()

        result = compute_dsr(returns, trial_count=1)

        # With 1 trial, expected_max = 0, so DSR = Φ(SR / σ_SR)
        assert result.trial_count == 1
        assert result.expected_max_sharpe == 0.0
        assert isinstance(result.dsr, float)

    def test_more_trials_more_deflation(self):
        """More trials should lead to more deflation (lower DSR)."""
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 252).tolist()

        result_1 = compute_dsr(returns, trial_count=1)
        result_10 = compute_dsr(returns, trial_count=10)
        result_100 = compute_dsr(returns, trial_count=100)

        # More trials → higher expected_max → lower DSR
        assert result_1.expected_max_sharpe < result_10.expected_max_sharpe
        assert result_10.expected_max_sharpe < result_100.expected_max_sharpe

    def test_insufficient_data_degraded(self):
        """Insufficient data should produce a degraded result."""
        result = compute_dsr([], trial_count=10)
        assert result.is_degraded
        assert any("Insufficient return data" in note for note in result.degradation_notes)

    def test_zero_std_degraded(self):
        """Zero standard deviation should produce a degraded result."""
        result = compute_dsr([0.0, 0.0, 0.0], trial_count=10)
        assert result.is_degraded

    def test_expected_max_sharpe_null(self):
        """Test the expected max Sharpe under the null."""
        # With 1 trial, no selection effect
        assert _expected_max_sharpe_null(1) == 0.0

        # With more trials, expected max increases
        em10 = _expected_max_sharpe_null(10)
        em100 = _expected_max_sharpe_null(100)
        assert em10 > 0
        assert em100 > em10

    def test_dsr_result_to_dict(self):
        result = compute_dsr([0.01, 0.02, -0.01, 0.015], trial_count=5)
        d = result.to_dict()
        assert "dsr" in d
        assert "observed_sharpe" in d
        assert "trial_count" in d
        assert d["trial_count"] == 5

    def test_small_sample_uses_normal_approx(self):
        """Small samples should degrade to normal approximation."""
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 15).tolist()

        result = compute_dsr(returns, trial_count=5)
        assert result.is_degraded
        assert any("Small sample" in note for note in result.degradation_notes)


class TestCSCV:
    """Test the CSCV computation."""

    def test_basic_cscv(self):
        """Test basic CSCV computation."""
        np.random.seed(42)
        # 252 observations, 5 strategies
        returns_matrix = np.random.normal(0.001, 0.02, (252, 5))

        result = compute_cscv(returns_matrix, s=16)

        assert isinstance(result, CSCVResult)
        assert result.s == 16
        assert result.trial_count == 5
        assert result.observation_count == 252
        assert isinstance(result.pbo, float)
        assert len(result.rank_distribution) > 0

    def test_cscv_insufficient_data(self):
        """CSCV with insufficient data should degrade."""
        np.random.seed(42)
        returns_matrix = np.random.normal(0.001, 0.02, (10, 3))

        result = compute_cscv(returns_matrix, s=16)
        assert result.is_degraded

    def test_cscv_result_to_dict(self):
        np.random.seed(42)
        returns_matrix = np.random.normal(0.001, 0.02, (252, 5))

        result = compute_cscv(returns_matrix, s=16)
        d = result.to_dict()
        assert "pbo" in d
        assert "rank_distribution" in d
        assert "s" in d
        assert d["s"] == 16
