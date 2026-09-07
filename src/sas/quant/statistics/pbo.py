"""Probability of Backtest Overfitting (PBO) via CSCV.

PBO estimates the probability that the strategy selected as best in-sample
will perform poorly out-of-sample. This implementation uses the
combinatorially symmetric cross-validation (CSCV) framework from Bailey
& López de Prado (2014).

The PBO is computed as:

    PBO = logit(proportion of times IS-best strategy has below-median OOS performance)

Where the logit transform maps the proportion to the real line, giving
a measure of selection bias. A PBO close to 0 means the IS-best strategy
is equally likely to be above or below median OOS. A positive PBO means
the IS-best strategy is more likely to underperform OOS — evidence of
backtest overfitting.

Reference:
    Bailey, D.H., Borwein, J.M., López de Prado, M., and Zhu, Q.J. (2014).
    "Pseudo-Mathematics and Financial Charlatanism: The Effects of
    Backtest Overfitting on Out-of-Sample Performance."
    Notices of the American Mathematical Society.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from sas.quant.statistics.cscv import CSCVResult, compute_cscv, compute_cscv_from_trials


@dataclass(frozen=True)
class PBOResult:
    """Result of a PBO computation."""

    pbo: float  # Probability of Backtest Overfitting (logit scale)
    pbo_proportion: float  # Raw proportion (before logit)
    cscv_result: CSCVResult | None = None
    trial_count: int = 0
    observation_count: int = 0
    methodology: str = "bailey_lopez_de_prado_2014_cscv"
    is_degraded: bool = False
    degradation_notes: list[str] = field(default_factory=list)
    assumptions: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "pbo": self.pbo,
            "pbo_proportion": self.pbo_proportion,
            "cscv_result": self.cscv_result.to_dict() if self.cscv_result else None,
            "trial_count": self.trial_count,
            "observation_count": self.observation_count,
            "methodology": self.methodology,
            "is_degraded": self.is_degraded,
            "degradation_notes": list(self.degradation_notes),
            "assumptions": dict(self.assumptions),
        }


def compute_pbo(
    returns_matrix: np.ndarray,
    s: int = 16,
) -> PBOResult:
    """Compute PBO from a returns matrix.

    Args:
        returns_matrix: (T, N) array of returns — T observations, N strategies.
        s: Number of partitions for CSCV (must be even).

    Returns:
        PBOResult with PBO and metadata.
    """
    cscv_result = compute_cscv(returns_matrix, s=s)

    # PBO is the logit of the proportion of times IS-best has below-median OOS
    pbo = cscv_result.pbo
    proportion = cscv_result.pbo_proportion if hasattr(cscv_result, 'pbo_proportion') else 0.0

    # Recompute proportion from rank distribution
    if cscv_result.rank_distribution:
        below_median_count = sum(1 for r in cscv_result.rank_distribution if r > 0.5)
        proportion = below_median_count / len(cscv_result.rank_distribution)
    else:
        proportion = 0.0

    return PBOResult(
        pbo=pbo,
        pbo_proportion=proportion,
        cscv_result=cscv_result,
        trial_count=cscv_result.trial_count,
        observation_count=cscv_result.observation_count,
        is_degraded=cscv_result.is_degraded,
        degradation_notes=list(cscv_result.degradation_notes),
        assumptions=dict(cscv_result.assumptions),
    )


def compute_pbo_from_trials(trials: list, s: int = 16) -> PBOResult:
    """Compute PBO from a list of trial artifacts.

    Extracts return series from each trial and constructs the returns matrix.
    """
    cscv_result = compute_cscv_from_trials(trials, s=s)

    # Recompute proportion from rank distribution
    if cscv_result.rank_distribution:
        below_median_count = sum(1 for r in cscv_result.rank_distribution if r > 0.5)
        proportion = below_median_count / len(cscv_result.rank_distribution)
    else:
        proportion = 0.0

    return PBOResult(
        pbo=cscv_result.pbo,
        pbo_proportion=proportion,
        cscv_result=cscv_result,
        trial_count=cscv_result.trial_count,
        observation_count=cscv_result.observation_count,
        is_degraded=cscv_result.is_degraded,
        degradation_notes=list(cscv_result.degradation_notes),
        assumptions=dict(cscv_result.assumptions),
    )
