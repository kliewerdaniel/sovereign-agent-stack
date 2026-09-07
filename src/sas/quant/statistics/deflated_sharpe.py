"""Deflated Sharpe Ratio — Bailey & López de Prado (2012) formulation.

The DSR corrects for selection effects, non-normal returns, and multiple
strategy configurations. It is defined as:

    DSR = Φ((SR - SR*) / σ_SR)

Where:
    SR  = observed annualized Sharpe ratio
    SR* = expected maximum Sharpe ratio under the null (all strategies have E[SR]=0)
    σ_SR = standard error of the Sharpe ratio estimate
    Φ   = standard normal CDF

The expected maximum under the null accounts for the fact that when you
test N strategies and pick the best, the reported Sharpe is inflated.
SR* = E[max{SR_1, ..., SR_N} | H0]

Reference:
    Bailey, D.H. and López de Prado, M. (2012). "The Deflated Sharpe Ratio:
    Correcting for Selection Bias, Nonnormality, and Serial Correlation."
    Journal of Portfolio Management.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy import stats


# Euler-Mascheroni constant
GAMMA = 0.5772156649015329


@dataclass(frozen=True)
class DSRResult:
    """Result of a Deflated Sharpe Ratio computation."""

    dsr: float  # The deflated Sharpe ratio (probability value)
    observed_sharpe: float  # The observed annualized Sharpe ratio
    expected_max_sharpe: float  # SR* — expected maximum under null
    standard_error: float  # σ_SR — standard error of Sharpe estimate
    trial_count: int  # N — number of eligible trials
    observation_count: int  # T — number of return observations
    methodology: str = "bailey_lopez_de_prado_2012"
    is_degraded: bool = False
    degradation_notes: list[str] = field(default_factory=list)
    assumptions: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "dsr": self.dsr,
            "observed_sharpe": self.observed_sharpe,
            "expected_max_sharpe": self.expected_max_sharpe,
            "standard_error": self.standard_error,
            "trial_count": self.trial_count,
            "observation_count": self.observation_count,
            "methodology": self.methodology,
            "is_degraded": self.is_degraded,
            "degradation_notes": list(self.degradation_notes),
            "assumptions": dict(self.assumptions),
        }


def _expected_max_sharpe_null(trial_count: int) -> float:
    """Compute the expected maximum Sharpe ratio under the null hypothesis.

    For N independent standard normal variables, the expected maximum is
    approximated using extreme value theory:

        E[max{Z_1, ..., Z_N}] ≈ Φ^{-1}(1 - 1/N) + γ * (1 - Φ^{-1}(1 - 1/N)^2) / (2 * Φ^{-1}(1 - 1/N))

    Where γ is the Euler-Mascheroni constant.

    For N = 1, this returns 0.0 (no selection effect).
    """
    if trial_count <= 1:
        return 0.0

    # Inverse normal CDF at (1 - 1/N)
    z = stats.norm.ppf(1.0 - 1.0 / trial_count)

    # Euler-Mascheroni correction
    correction = GAMMA * (1.0 - z**2) / (2.0 * z) if z != 0.0 else 0.0

    return z + correction


def _standard_error_sharpe(
    returns: list[float],
    observed_sharpe: float,
) -> float:
    """Compute the standard error of the Sharpe ratio estimate.

    From Bailey & López de Prado (2012):

        σ_SR = sqrt( (1 + 0.5*SR^2 - skew*SR + (kurt-3)/4*SR^2) / (T-1) )

    Where:
        SR    = observed annualized Sharpe ratio
        skew  = skewness of returns
        kurt  = excess kurtosis of returns
        T     = number of observations

    If T is too small for reliable skewness/kurtosis estimates, falls back
    to the normal approximation (skew=0, kurt=3).
    """
    if not returns or len(returns) < 3:
        return float("inf")

    r = np.array(returns, dtype=float)
    T = len(r)

    # Minimum observations for reliable skewness/kurtosis estimation
    MIN_OBS_FOR_MOMENTS = 30

    if T >= MIN_OBS_FOR_MOMENTS:
        skew = float(stats.skew(r, bias=False))
        kurt = float(stats.kurtosis(r, bias=False))  # excess kurtosis
    else:
        # Fall back to normal approximation
        skew = 0.0
        kurt = 0.0

    # Variance of the Sharpe ratio (annualized)
    sr_daily = observed_sharpe / math.sqrt(252) if observed_sharpe != 0 else 0.0
    variance = (
        1.0
        + 0.5 * sr_daily**2
        - skew * sr_daily
        + (kurt - 3.0) / 4.0 * sr_daily**2
    ) / (T - 1)

    # Annualize the standard error
    if variance <= 0:
        return 0.0

    return math.sqrt(variance) * math.sqrt(252)


def compute_dsr(
    returns: list[float],
    trial_count: int,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> DSRResult:
    """Compute the Deflated Sharpe Ratio.

    Args:
        returns: Daily return series of the selected strategy.
        trial_count: Number of eligible trials (N) — the actual number of
            evaluated strategies, not a configured maximum.
        risk_free_rate: Annual risk-free rate.
        periods_per_year: Number of trading periods per year (252 for daily).

    Returns:
        DSRResult with the deflated Sharpe ratio and metadata.
    """
    degradation_notes = []
    assumptions = {
        "risk_free_rate": risk_free_rate,
        "periods_per_year": periods_per_year,
        "null_hypothesis": "all strategies have zero expected Sharpe ratio",
    }

    # Check for sufficient data
    if not returns or len(returns) < 2:
        return DSRResult(
            dsr=0.0,
            observed_sharpe=0.0,
            expected_max_sharpe=0.0,
            standard_error=float("inf"),
            trial_count=trial_count,
            observation_count=len(returns) if returns else 0,
            is_degraded=True,
            degradation_notes=["Insufficient return data (need at least 2 observations)"],
            assumptions=assumptions,
        )

    # Compute observed annualized Sharpe ratio
    r = np.array(returns, dtype=float)
    T = len(r)
    daily_rf = risk_free_rate / periods_per_year
    excess = r - daily_rf
    mean_excess = float(np.mean(excess))
    std_excess = float(np.std(excess, ddof=1))

    if std_excess == 0.0:
        return DSRResult(
            dsr=0.0,
            observed_sharpe=0.0,
            expected_max_sharpe=0.0,
            standard_error=0.0,
            trial_count=trial_count,
            observation_count=T,
            is_degraded=True,
            degradation_notes=["Zero standard deviation in returns"],
            assumptions=assumptions,
        )

    observed_sharpe = (mean_excess / std_excess) * math.sqrt(periods_per_year)

    # Compute expected maximum under null
    expected_max = _expected_max_sharpe_null(trial_count)

    # Compute standard error
    se = _standard_error_sharpe(returns, observed_sharpe)

    # Check if we degraded to normal approximation
    if T < 30:
        degradation_notes.append(
            f"Small sample (T={T} < 30): using normal approximation "
            f"for skewness and kurtosis"
        )
        assumptions["skewness"] = 0.0
        assumptions["excess_kurtosis"] = 0.0
    else:
        assumptions["skewness"] = float(stats.skew(r, bias=False))
        assumptions["excess_kurtosis"] = float(stats.kurtosis(r, bias=False))

    # Compute DSR
    if se == 0.0 or math.isinf(se):
        dsr = 0.0
        degradation_notes.append("Standard error is zero or infinite")
    else:
        z_score = (observed_sharpe - expected_max) / se
        dsr = float(stats.norm.cdf(z_score))

    return DSRResult(
        dsr=dsr,
        observed_sharpe=observed_sharpe,
        expected_max_sharpe=expected_max,
        standard_error=se,
        trial_count=trial_count,
        observation_count=T,
        is_degraded=len(degradation_notes) > 0,
        degradation_notes=degradation_notes,
        assumptions=assumptions,
    )


def compute_dsr_from_trial(trial, trial_count: int) -> DSRResult:
    """Compute DSR from a trial artifact.

    Uses the trial's return series and the actual trial count from the ledger.
    """
    returns = trial.return_series if trial.return_series else []
    return compute_dsr(returns, trial_count)
