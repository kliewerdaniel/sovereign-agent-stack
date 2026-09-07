"""Substrate validation — characterize finite-sample behavior of the DGP.

The synthetic world generator declares parameters (signal_strength,
autocorrelation). Any single finite-sample realization will differ from
the declaration due to sampling noise. Before declaring the substrate
valid, we must establish the empirical distribution of realized
autocorrelation for each parameterization.

This lets us answer: "When we declare AR=0, what range of measured
autocorrelation is consistent with that declaration?" If a measured
value falls outside the 95% interval, the world is an outlier — not
a valid instance of the declared DGP.

Key invariant:

    measured_autocorrelation falls within empirically established
    null distribution of declared_autocorrelation

NOT:

    measured_autocorrelation == declared_autocorrelation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd

from sas.quant.experiment.synthetic_worlds import (
    generate_known_signal_world,
    generate_null_world,
)


# ---------------------------------------------------------------------------
# Empirical distribution of realized statistics
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RealizedDistribution:
    """Empirical distribution of a realized statistic across repeated worlds.

    For a given (signal_strength, autocorrelation) declaration, we generate
    N worlds with different seeds and measure the realized autocorrelation
    of each. This gives us the sampling distribution of the statistic.

    Attributes:
        declared_signal: The declared signal_strength parameter.
        declared_autocorrelation: The declared AR(1) coefficient parameter.
        n_worlds: Number of worlds generated.
        realized_values: Array of measured autocorrelations.
        mean: Mean of realized values.
        std: Standard deviation of realized values.
        ci_lower: 2.5th percentile (95% CI lower bound).
        ci_upper: 97.5th percentile (95% CI upper bound).
        median: 50th percentile.
    """

    declared_signal: float
    declared_autocorrelation: float
    n_worlds: int
    realized_values: list[float] = field(default_factory=list)
    mean: float = 0.0
    std: float = 0.0
    ci_lower: float = 0.0
    ci_upper: float = 0.0
    median: float = 0.0

    def to_dict(self) -> dict:
        return {
            "declared_signal": self.declared_signal,
            "declared_autocorrelation": self.declared_autocorrelation,
            "n_worlds": self.n_worlds,
            "mean": self.mean,
            "std": self.std,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "median": self.median,
            "realized_values": list(self.realized_values),
        }

    def contains(self, value: float) -> bool:
        """Check whether a measured value falls within the 95% CI."""
        return self.ci_lower <= value <= self.ci_upper


def characterize_substrate(
    signal_strengths: list[float] | None = None,
    autocorrelations: list[float] | None = None,
    n_worlds: int = 200,
    n_observations: int = 252,
    noise_std: float = 0.02,
    base_seed: int = 42,
) -> dict[str, RealizedDistribution]:
    """Characterize the empirical distribution of realized autocorrelation.

    For each (signal_strength, autocorrelation) combination, generate N
    worlds with different seeds and measure the realized autocorrelation.
    This establishes the null distribution for each parameterization.

    Args:
        signal_strengths: Signal strengths to test.
        autocorrelations: AR(1) coefficients to test.
        n_worlds: Number of worlds per parameter combination.
        n_observations: Observations per world.
        noise_std: Noise standard deviation.
        base_seed: Base random seed.

    Returns:
        Dict mapping parameter key to RealizedDistribution.
    """
    if signal_strengths is None:
        signal_strengths = [0.0, 0.1, 0.25, 0.5, 1.0]
    if autocorrelations is None:
        autocorrelations = [0.0, 0.3, 0.5]

    distributions: dict[str, RealizedDistribution] = {}

    for signal_strength in signal_strengths:
        for autocorrelation in autocorrelations:
            key = f"s{signal_strength}-ar{autocorrelation}"
            realized = []

            for i in range(n_worlds):
                seed = base_seed + i
                if signal_strength == 0.0:
                    world = generate_null_world(
                        world_id=f"char-{key}-{i}",
                        noise_std=noise_std,
                        autocorrelation=autocorrelation,
                        seed=seed,
                    )
                else:
                    world, _ = generate_known_signal_world(
                        world_id=f"char-{key}-{i}",
                        signal_strength=signal_strength,
                        noise_std=noise_std,
                        autocorrelation=autocorrelation,
                        n_observations=n_observations,
                        seed=seed,
                    )

                autocorr = world.research_data["returns"].autocorr(lag=1)
                realized.append(float(autocorr))

            arr = np.array(realized)
            distributions[key] = RealizedDistribution(
                declared_signal=signal_strength,
                declared_autocorrelation=autocorrelation,
                n_worlds=n_worlds,
                realized_values=realized,
                mean=float(np.mean(arr)),
                std=float(np.std(arr)),
                ci_lower=float(np.percentile(arr, 2.5)),
                ci_upper=float(np.percentile(arr, 97.5)),
                median=float(np.median(arr)),
            )

    return distributions


# ---------------------------------------------------------------------------
# Report Generator
# ---------------------------------------------------------------------------


def generate_substrate_characterization_report(
    distributions: dict[str, RealizedDistribution],
) -> str:
    """Generate a report of the substrate characterization."""
    lines = [
        "# Substrate Characterization Report",
        "",
        "Empirical distribution of realized autocorrelation across repeated worlds.",
        "",
        "For each declared parameter combination, we generate N worlds with",
        "different seeds and measure the realized autocorrelation.",
        "",
        "## Declared vs Realized Autocorrelation",
        "",
        "| Declared Signal | Declared AR | Mean Realized AR | Std | 95% CI | Median |",
        "|---|---|---|---|---|---|",
    ]

    for key, d in sorted(distributions.items()):
        lines.append(
            f"| {d.declared_signal:.2f} | {d.declared_autocorrelation:.2f} | "
            f"{d.mean:.4f} | {d.std:.4f} | "
            f"[{d.ci_lower:.4f}, {d.ci_upper:.4f}] | {d.median:.4f} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- **Declared AR = 0.0**: Measured autocorrelation should fall within the 95% CI.",
        "  If a world's measured AR is outside this interval, it is an outlier.",
        "- **Declared AR = 0.3 or 0.5**: Measured autocorrelation should be",
        "  approximately centered on the declared value.",
        "- The width of the interval reflects finite-sample sampling noise.",
        "  Longer time series → narrower interval → tighter control.",
        "",
        "---",
        "*Generated by SAS Substrate Validation Framework*",
    ])

    return "\n".join(lines )
