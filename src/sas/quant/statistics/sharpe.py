"""Standard Sharpe ratio — deterministic function over immutable artifacts.

This is the foundation for the Deflated Sharpe Ratio. The standard
Sharpe ratio is computed as the mean excess return divided by the
standard deviation of returns, annualized by sqrt(252) for daily data.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np


def annualized_sharpe_ratio(
    returns: list[float],
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """Compute the annualized Sharpe ratio from a series of returns.

    Args:
        returns: Daily return series.
        risk_free_rate: Annual risk-free rate (default 0.0).
        periods_per_year: Number of trading periods per year (252 for daily).

    Returns:
        Annualized Sharpe ratio. Returns 0.0 if std is 0 or insufficient data.
    """
    if not returns or len(returns) < 2:
        return 0.0

    r = np.array(returns, dtype=float)
    daily_rf = risk_free_rate / periods_per_year
    excess = r - daily_rf

    mean_excess = float(np.mean(excess))
    std_excess = float(np.std(excess, ddof=1))

    if std_excess == 0.0:
        return 0.0

    sharpe = mean_excess / std_excess
    return sharpe * math.sqrt(periods_per_year)


def sharpe_ratio_from_trial(trial) -> float | None:
    """Extract the Sharpe ratio from a trial artifact."""
    if trial.backtest_result and "sharpe_ratio" in trial.backtest_result:
        return trial.backtest_result["sharpe_ratio"]
    if trial.return_series:
        return annualized_sharpe_ratio(trial.return_series)
    return None
