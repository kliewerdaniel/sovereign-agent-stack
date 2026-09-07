"""Deterministic quantitative computation engine.

All core quant computations — returns, volatility, covariance, Sharpe,
Sortino, drawdown, beta, factor exposure — are pure numpy/pandas with
no LLM involvement.  Results are reproducible given the same inputs
and random seed.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class EngineConfig:
    """Deterministic engine configuration."""
    risk_free_rate: float = 0.02        # annual
    trading_days: int = 252
    min_periods: int = 20
    seed: int = 42


class QuantEngine:
    """Deterministic quantitative computation engine."""

    def __init__(self, config: EngineConfig | None = None):
        self.config = config or EngineConfig()
        self._rng = np.random.default_rng(self.config.seed)
        self._version = "1.0.0"

    # ── Returns ──────────────────────────────────────────────────

    def returns(self, prices: pd.Series | np.ndarray, method: str = "log") -> np.ndarray:
        """Compute returns from a price series."""
        p = np.asarray(prices, dtype=float)
        if method == "log":
            return np.diff(np.log(p))
        elif method == "simple":
            return np.diff(p) / p[:-1]
        else:
            raise ValueError(f"Unknown method: {method}")

    def cumulative_returns(self, returns: np.ndarray) -> np.ndarray:
        """Cumulative returns from period returns."""
        return np.exp(np.cumsum(returns)) - 1 if self._is_log(returns) else np.cumprod(1 + returns) - 1

    def annualized_return(self, returns: np.ndarray) -> float:
        """Annualized return."""
        if len(returns) == 0:
            return 0.0
        total = np.prod(1 + returns) if not self._is_log(returns) else np.exp(np.sum(returns))
        years = len(returns) / self.config.trading_days
        return float(total ** (1 / years) - 1) if years > 0 else 0.0

    # ── Risk ─────────────────────────────────────────────────────

    def volatility(self, returns: np.ndarray, annualized: bool = True) -> float:
        """Standard deviation of returns."""
        if len(returns) < 2:
            return 0.0
        vol = float(np.std(returns, ddof=1))
        return vol * np.sqrt(self.config.trading_days) if annualized else vol

    def downside_risk(self, returns: np.ndarray, mar: float = 0.0,
                      annualized: bool = True) -> float:
        """Downside deviation (Semi-deviation below MAR)."""
        r = np.asarray(returns)
        below = r[r < mar]
        if len(below) < 2:
            return 0.0
        dr = float(np.sqrt(np.mean((below - mar) ** 2)))
        return dr * np.sqrt(self.config.trading_days) if annualized else dr

    def sharpe(self, returns: np.ndarray, rf: float | None = None) -> float:
        """Sharpe ratio."""
        rf = rf or self.config.risk_free_rate
        vol = self.volatility(returns)
        if vol == 0:
            return 0.0
        ret = self.annualized_return(returns)
        return (ret - rf) / vol

    def sortino(self, returns: np.ndarray, rf: float | None = None) -> float:
        """Sortino ratio (downside risk instead of total vol)."""
        rf = rf or self.config.risk_free_rate
        dr = self.downside_risk(returns)
        if dr == 0:
            return 0.0
        ret = self.annualized_return(returns)
        return (ret - rf) / dr

    def max_drawdown(self, returns: np.ndarray) -> dict:
        """Maximum drawdown and duration."""
        cum = np.concatenate([[0], np.cumsum(returns)])
        peak = np.maximum.accumulate(cum)
        trough = cum - peak
        max_dd = float(np.min(trough))
        # Duration
        below = trough < 0
        if not np.any(below):
            duration = 0
        else:
            # longest consecutive run below zero
            runs = np.diff(np.concatenate([[0], below.astype(int), [0]]))
            starts = np.where(runs > 0)[0]
            ends = np.where(runs < 0)[0]
            duration = int(max(ends - starts)) if len(starts) else 0
        return {"max_drawdown": max_dd, "duration_days": duration,
                "recovery_days": duration}

    def var(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """Value at Risk (historical)."""
        if len(returns) == 0:
            return 0.0
        return float(np.percentile(returns, (1 - confidence) * 100))

    def cvar(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """Conditional VaR (expected shortfall)."""
        if len(returns) == 0:
            return 0.0
        var = self.var(returns, confidence)
        return float(np.mean(returns[returns <= var]))

    # ── Portfolio ────────────────────────────────────────────────

    def portfolio_return(self, weights: np.ndarray, expected_returns: np.ndarray) -> float:
        """Portfolio expected return: w' * μ."""
        return float(np.dot(weights, expected_returns))

    def portfolio_volatility(self, weights: np.ndarray, cov_matrix: np.ndarray) -> float:
        """Portfolio volatility: sqrt(w' * Σ * w)."""
        return float(np.sqrt(np.dot(weights, np.dot(cov_matrix, weights))))

    def covariance(self, returns: pd.DataFrame) -> pd.DataFrame:
        """Covariance matrix of returns."""
        return returns.cov()

    def correlation(self, returns: pd.DataFrame) -> pd.DataFrame:
        """Correlation matrix of returns."""
        return returns.corr()

    def beta(self, returns: np.ndarray, benchmark: np.ndarray) -> float:
        """Beta of returns vs benchmark."""
        if len(returns) != len(benchmark) or len(returns) < 2:
            return 0.0
        cov = np.cov(returns, benchmark, ddof=0)
        var_b = cov[1, 1]
        if var_b == 0:
            return 0.0
        return float(cov[0, 0] / var_b)

    def factor_exposure(self, returns: np.ndarray, factors: np.ndarray) -> np.ndarray:
        """Regression-based factor exposure (OLS)."""
        if len(returns) < 2 or factors.shape[0] != len(returns):
            return np.array([])
        F = np.column_stack([np.ones(len(returns)), factors])
        try:
            beta = np.linalg.lstsq(F, returns, rcond=None)[0]
            return beta
        except np.linalg.LinAlgError:
            return np.zeros(F.shape[1])

    # ── Attribution ──────────────────────────────────────────────

    def attribution(self, portfolio_returns: np.ndarray,
                    factor_returns: np.ndarray) -> dict:
        """Simple factor attribution via regression."""
        if len(portfolio_returns) != len(factor_returns):
            return {"error": "length mismatch"}
        beta = self.beta(portfolio_returns, factor_returns)
        residual = portfolio_returns - beta * factor_returns
        return {
            "beta": beta,
            "factor_contribution": float(beta * np.mean(factor_returns) * self.config.trading_days),
            "residual_vol": float(np.std(residual, ddof=1) * np.sqrt(self.config.trading_days)),
            "information_ratio": float(np.mean(residual) / (np.std(residual, ddof=1) + 1e-12) * np.sqrt(self.config.trading_days)),
        }

    # ── Helpers ──────────────────────────────────────────────────

    def _is_log(self, returns: np.ndarray) -> bool:
        """Heuristic: log returns have smaller magnitude."""
        return np.max(np.abs(returns)) < 1.0

    def check_reproducibility(self, computation_hash: str,
                              expected_hash: str | None = None) -> bool:
        """Verify computation hash matches expected (determinism gate)."""
        if expected_hash is None:
            return True
        return computation_hash == expected_hash

    def version(self) -> str:
        return self._version