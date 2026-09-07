"""Combinatorially Symmetric Cross-Validation (CSCV) — Bailey & López de Prado (2014).

CSCV estimates the probability that the strategy selected as best in-sample
will perform poorly out-of-sample. It works by:

1. Splitting the return series into S equally sized partitions.
2. Considering all possible combinations of S/2 partitions for IS, S/2 for OOS.
3. For each combination, computing the relative rank of the IS-best strategy
   in OOS performance.
4. Constructing the distribution of out-of-sample ranks.

The Probability of Backtest Overfitting (PBO) is the logit of the proportion
of times the IS-best strategy has below-median OOS performance.

Reference:
    Bailey, D.H., Borwein, J.M., López de Prado, M., and Zhu, Q.J. (2014).
    "Pseudo-Mathematics and Financial Charlatanism: The Effects of
    Backtest Overfitting on Out-of-Sample Performance."
    Notices of the American Mathematical Society.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import combinations
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class CSCVResult:
    """Result of a CSCV computation."""

    pbo: float  # Probability of Backtest Overfitting
    pbo_proportion: float  # Raw proportion (before logit)
    rank_distribution: list[float]  # Distribution of OOS ranks
    s: int  # Number of partitions
    trial_count: int  # Number of strategies (trials)
    observation_count: int  # Number of return observations
    methodology: str = "bailey_lopez_de_prado_2014_cscv"
    is_degraded: bool = False
    degradation_notes: list[str] = field(default_factory=list)
    assumptions: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "pbo": self.pbo,
            "pbo_proportion": self.pbo_proportion,
            "rank_distribution": [round(r, 4) for r in self.rank_distribution],
            "s": self.s,
            "trial_count": self.trial_count,
            "observation_count": self.observation_count,
            "methodology": self.methodology,
            "is_degraded": self.is_degraded,
            "degradation_notes": list(self.degradation_notes),
            "assumptions": dict(self.assumptions),
        }


def _compute_sharpe_vector(returns: np.ndarray) -> np.ndarray:
    """Compute the Sharpe ratio for each strategy (column) in the returns matrix."""
    T = returns.shape[0]
    if T < 2:
        return np.zeros(returns.shape[1])

    mean = np.mean(returns, axis=0)
    std = np.std(returns, axis=0, ddof=1)
    std[std == 0] = 1e-10
    return (mean / std) * np.sqrt(252)


def compute_cscv(
    returns_matrix: np.ndarray,
    s: int = 16,
) -> CSCVResult:
    """Compute CSCV-based PBO.

    Args:
        returns_matrix: (T, N) array of returns — T observations, N strategies.
        s: Number of partitions (must be even). Default 16.

    Returns:
        CSCVResult with PBO and metadata.
    """
    degradation_notes = []
    assumptions = {
        "s": s,
        "performance_metric": "annualized_sharpe_ratio",
        "null_hypothesis": "IS-best strategy has no selection bias",
    }

    T, N = returns_matrix.shape

    if T < 2 * s:
        degradation_notes.append(
            f"Insufficient observations (T={T}) for S={s} partitions. "
            f"Need at least {2*s} observations."
        )
        s = max(2, T // 2)
        s = s if s % 2 == 0 else s - 1
        if s < 2:
            return CSCVResult(
                pbo=0.0,
                pbo_proportion=0.0,
                rank_distribution=[],
                s=s,
                trial_count=N,
                observation_count=T,
                is_degraded=True,
                degradation_notes=degradation_notes + ["Cannot compute CSCV with S < 2"],
                assumptions=assumptions,
            )

    # Split into S partitions
    partition_size = T // s
    partitions = []
    for i in range(s):
        start = i * partition_size
        end = start + partition_size if i < s - 1 else T
        partitions.append(returns_matrix[start:end, :])

    # All combinations of S/2 partitions for IS
    half_s = s // 2
    is_combinations = list(combinations(range(s), half_s))

    rank_distribution = []

    for is_indices in is_combinations:
        oos_indices = [i for i in range(s) if i not in is_indices]

        is_returns = np.vstack([partitions[i] for i in is_indices])
        oos_returns = np.vstack([partitions[i] for i in oos_indices])

        is_sharpes = _compute_sharpe_vector(is_returns)
        oos_sharpes = _compute_sharpe_vector(oos_returns)

        is_best_idx = int(np.argmax(is_sharpes))

        # OOS rank: fraction of strategies that outperform IS-best
        oos_rank = float(np.sum(oos_sharpes > oos_sharpes[is_best_idx]) / N)
        rank_distribution.append(oos_rank)

    # PBO = logit(proportion of times IS-best has below-median OOS performance)
    below_median_count = sum(1 for r in rank_distribution if r > 0.5)
    proportion = below_median_count / len(rank_distribution) if rank_distribution else 0.0

    if proportion <= 0.0:
        proportion = 1e-10
    elif proportion >= 1.0:
        proportion = 1.0 - 1e-10

    pbo = math.log(proportion / (1.0 - proportion))

    return CSCVResult(
        pbo=pbo,
        pbo_proportion=proportion,
        rank_distribution=rank_distribution,
        s=s,
        trial_count=N,
        observation_count=T,
        is_degraded=len(degradation_notes) > 0,
        degradation_notes=degradation_notes,
        assumptions=assumptions,
    )


def compute_cscv_from_trials(trials: list, s: int = 16) -> CSCVResult:
    """Compute CSCV from a list of trial artifacts."""
    valid_trials = [t for t in trials if t.return_series and len(t.return_series) > 1]

    if not valid_trials:
        return CSCVResult(
            pbo=0.0,
            pbo_proportion=0.0,
            rank_distribution=[],
            s=s,
            trial_count=0,
            observation_count=0,
            is_degraded=True,
            degradation_notes=["No trials with valid return series"],
            assumptions={},
        )

    min_len = min(len(t.return_series) for t in valid_trials)
    returns_matrix = np.array([t.return_series[:min_len] for t in valid_trials]).T

    return compute_cscv(returns_matrix, s=s)
