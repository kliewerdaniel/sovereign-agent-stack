"""Synthetic worlds with independently controlled data generating processes.

These worlds enable controlled experiments where the true data generating
process is known. This allows us to distinguish between:

1. Architecture exposing overfitting vs. correctly measuring it
2. Agent optimization pressure vs. genuine signal recovery
3. Selection effects vs. true predictive structure
4. Signal-driven edge vs. serial-dependence-driven edge

The critical design principle: signal strength, volatility, and serial
dependence are INDEPENDENTLY controllable. This lets us distinguish whether
an agent is discovering the declared signal or merely exploiting predictable
structure (autocorrelation).

World types:

- Null IID: No signal, no autocorrelation (pure random walk)
- Null AR: No signal, but autocorrelation exists (momentum edge possible)
- Signal IID: Known signal, no autocorrelation
- Signal AR: Known signal + autocorrelation (two sources of edge)

The confounder matrix:

| World | Signal | Autocorrelation | Expected |
|---|---:|---:|---|
| Null IID | 0 | 0 | No edge |
| Null AR | 0 | 0.5 | Momentum edge possible |
| Signal IID | 0.5 | 0 | Known edge |
| Signal + AR | 0.5 | 0.5 | Known edge + persistence |
| Strong signal IID | 1.0 | 0 | Strong edge |
| Strong signal + AR | 1.0 | 0.5 | Strong edge + persistence |

This lets us attribute mechanism: if momentum explodes in Null AR, the agent
isn't finding alpha — it's finding serial dependence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DataGeneratingProcess:
    """Description of the true data generating process.

    This is the ground truth that the agent does not have access to.
    It is used only for experimental validation.

    Key invariant: signal_strength, volatility, and autocorrelation are
    INDEPENDENT dimensions. Changing one does not change the others.
    """
    has_signal: bool
    signal_type: str  # "momentum", "mean_reversion", "known_sine", "none"
    signal_strength: float  # 0.0 to 1.0 (fraction of variance explained by signal)
    noise_std: float  # Volatility of the noise component
    autocorrelation: float  # Serial dependence (AR(1) coefficient), 0 = IID
    n_observations: int
    noise_distribution: str = "normal"  # "normal", "t"
    information_horizon: str = "t+1"  # How far ahead the signal predicts
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "has_signal": self.has_signal,
            "signal_type": self.signal_type,
            "signal_strength": self.signal_strength,
            "noise_std": self.noise_std,
            "autocorrelation": self.autocorrelation,
            "n_observations": self.n_observations,
            "noise_distribution": self.noise_distribution,
            "information_horizon": self.information_horizon,
            "description": self.description,
        }


@dataclass(frozen=True)
class SyntheticWorld:
    """A synthetic experimental world with known ground truth.

    The world provides price data for research and holdout windows,
    and records the true data generating process for later validation.

    Observable features are what the agent/researcher can see.
    Hidden features (signal, true_autocorrelation) are ground truth
    used only for experimental validation.
    """
    world_id: str
    symbol: str
    research_window: tuple[str, str]
    holdout_window: tuple[str, str]
    research_data: pd.DataFrame
    holdout_data: pd.DataFrame
    dgp: DataGeneratingProcess
    seed: int

    # Ground truth (not visible to the agent)
    research_signal: list[float] = field(default_factory=list)
    holdout_signal: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "world_id": self.world_id,
            "symbol": self.symbol,
            "research_window": list(self.research_window),
            "holdout_window": list(self.holdout_window),
            "dgp": self.dgp.to_dict(),
            "seed": self.seed,
            "research_observations": len(self.research_data),
            "holdout_observations": len(self.holdout_data),
        }


def _generate_noise(
    n: int,
    rng: np.random.Generator,
    noise_std: float,
    distribution: str = "normal",
) -> np.ndarray:
    """Generate noise with the specified distribution."""
    if distribution == "t":
        # Student's t with 5 degrees of freedom (fat tails)
        return rng.standard_t(df=5, size=n) * noise_std
    else:
        return rng.normal(0, noise_std, n)


def _generate_autocorrelated_noise(
    n: int,
    rng: np.random.Generator,
    noise_std: float,
    ar_coefficient: float,
    distribution: str = "normal",
) -> np.ndarray:
    """Generate autocorrelated noise using AR(1) process.

    e_t = ar_coefficient * e_{t-1} + eps_t

    This creates serial dependence WITHOUT injecting a predictable signal.
    The autocorrelation is a property of the noise, not a signal.
    """
    noise = _generate_noise(n, rng, noise_std, distribution)
    ar_noise = np.zeros(n)
    ar_noise[0] = noise[0]
    for i in range(1, n):
        ar_noise[i] = ar_coefficient * ar_noise[i - 1] + noise[i]
    return ar_noise


def generate_signal_world(
    world_id: str,
    symbol: str = "SYNTH",
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    research_fraction: float = 0.8,
    signal_type: str = "momentum",
    signal_strength: float = 0.15,
    noise_std: float = 0.02,
    autocorrelation: float = 0.0,
    noise_distribution: str = "normal",
    seed: int = 42,
) -> SyntheticWorld:
    """Generate a synthetic world with a known predictable signal.

    The signal is INDEPENDENT of autocorrelation. The signal is a predictable
    component that an oracle can exploit. Autocorrelation is serial dependence
    in the noise that creates momentum-like structure.

    Args:
        world_id: Unique identifier
        symbol: Ticker symbol
        start_date: Start date for the full period
        end_date: End date for the full period
        research_fraction: Fraction of data for research (rest is holdout)
        signal_type: Type of signal ("momentum", "mean_reversion", "known_sine")
        signal_strength: Fraction of variance explained by signal (0-1)
        noise_std: Standard deviation of the noise component
        autocorrelation: AR(1) coefficient for serial dependence (0 = IID)
        noise_distribution: Distribution of noise ("normal", "t")
        seed: Random seed for reproducibility

    Returns:
        SyntheticWorld with independently controlled signal and autocorrelation
    """
    rng = np.random.default_rng(seed)

    # Generate date range
    dates = pd.date_range(start_date, end_date, freq="B")
    n = len(dates)

    # Split into research and holdout
    research_end_idx = int(n * research_fraction)
    research_dates = dates[:research_end_idx]
    holdout_dates = dates[research_end_idx:]

    # Generate signal component (predictable, exploitable by oracle)
    if signal_type == "momentum":
        # Autocorrelated signal: r_t = signal_strength * r_{t-1} + eps
        signal_returns = np.zeros(n)
        for i in range(1, n):
            signal_returns[i] = signal_strength * signal_returns[i - 1] + rng.normal(0, noise_std)
    elif signal_type == "mean_reversion":
        # Mean-reverting signal: Ornstein-Uhlenbeck-like
        signal_returns = np.zeros(n)
        for i in range(1, n):
            signal_returns[i] = signal_returns[i - 1] - signal_strength * signal_returns[i - 1] + rng.normal(0, noise_std)
    elif signal_type == "known_sine":
        # Deterministic sine wave signal
        t = np.arange(n)
        signal_returns = signal_strength * 0.1 * np.sin(2 * np.pi * t / 50)
    else:
        signal_returns = np.zeros(n)

    # Generate autocorrelated noise (INDEPENDENT of signal)
    # This creates serial dependence that momentum strategies can exploit
    # but is NOT the declared signal
    noise_returns = _generate_autocorrelated_noise(
        n, rng, noise_std, autocorrelation, noise_distribution
    )

    # Combine: total returns = signal + autocorrelated noise
    total_returns = signal_returns + noise_returns

    # Convert to prices
    prices = 100 * np.exp(np.cumsum(total_returns))

    # Create DataFrames
    research_df = pd.DataFrame({
        "close": prices[:research_end_idx],
        "returns": total_returns[:research_end_idx],
        "signal": signal_returns[:research_end_idx],
    }, index=research_dates)

    holdout_df = pd.DataFrame({
        "close": prices[research_end_idx:],
        "returns": total_returns[research_end_idx:],
        "signal": signal_returns[research_end_idx:],
    }, index=holdout_dates)

    dgp = DataGeneratingProcess(
        has_signal=True,
        signal_type=signal_type,
        signal_strength=signal_strength,
        noise_std=noise_std,
        autocorrelation=autocorrelation,
        n_observations=n,
        noise_distribution=noise_distribution,
        description=(
            f"Signal world: {signal_type} with strength={signal_strength}, "
            f"noise_std={noise_std}, autocorrelation={autocorrelation}"
        ),
    )

    return SyntheticWorld(
        world_id=world_id,
        symbol=symbol,
        research_window=(str(research_dates[0].date()), str(research_dates[-1].date())),
        holdout_window=(str(holdout_dates[0].date()), str(holdout_dates[-1].date())),
        research_data=research_df,
        holdout_data=holdout_df,
        dgp=dgp,
        seed=seed,
        research_signal=signal_returns[:research_end_idx].tolist(),
        holdout_signal=signal_returns[research_end_idx:].tolist(),
    )


def generate_null_world(
    world_id: str,
    symbol: str = "NULL",
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    research_fraction: float = 0.8,
    noise_std: float = 0.02,
    autocorrelation: float = 0.0,
    noise_distribution: str = "normal",
    seed: int = 42,
) -> SyntheticWorld:
    """Generate a synthetic world with NO exploitable signal.

    This is a pure random walk (possibly with autocorrelation).
    Any strategy that appears to work in this world is manufacturing
    false discoveries through optimization pressure or exploiting
    serial dependence.

    The autocorrelation parameter lets us create "Null AR" worlds where
    momentum strategies can exploit serial dependence even though no
    declared signal exists.

    Args:
        world_id: Unique identifier
        symbol: Ticker symbol
        start_date: Start date for the full period
        end_date: End date for the full period
        research_fraction: Fraction of data for research (rest is holdout)
        noise_std: Standard deviation of returns
        autocorrelation: AR(1) coefficient for serial dependence (0 = IID)
        noise_distribution: Distribution of noise ("normal", "t")
        seed: Random seed for reproducibility

    Returns:
        SyntheticWorld with no signal (pure noise, possibly autocorrelated)
    """
    rng = np.random.default_rng(seed)

    # Generate date range
    dates = pd.date_range(start_date, end_date, freq="B")
    n = len(dates)

    # Split into research and holdout
    research_end_idx = int(n * research_fraction)
    research_dates = dates[:research_end_idx]
    holdout_dates = dates[research_end_idx:]

    # Generate autocorrelated noise (no signal component)
    returns = _generate_autocorrelated_noise(
        n, rng, noise_std, autocorrelation, noise_distribution
    )

    # Convert to prices
    prices = 100 * np.exp(np.cumsum(returns))

    # Create DataFrames
    research_df = pd.DataFrame({
        "close": prices[:research_end_idx],
        "returns": returns[:research_end_idx],
        "signal": np.zeros(research_end_idx),
    }, index=research_dates)

    holdout_df = pd.DataFrame({
        "close": prices[research_end_idx:],
        "returns": returns[research_end_idx:],
        "signal": np.zeros(n - research_end_idx),
    }, index=holdout_dates)

    dgp = DataGeneratingProcess(
        has_signal=False,
        signal_type="none",
        signal_strength=0.0,
        noise_std=noise_std,
        autocorrelation=autocorrelation,
        n_observations=n,
        noise_distribution=noise_distribution,
        description=(
            f"Null world: pure random walk, noise_std={noise_std}, "
            f"autocorrelation={autocorrelation}"
        ),
    )

    return SyntheticWorld(
        world_id=world_id,
        symbol=symbol,
        research_window=(str(research_dates[0].date()), str(research_dates[-1].date())),
        holdout_window=(str(holdout_dates[0].date()), str(holdout_dates[-1].date())),
        research_data=research_df,
        holdout_data=holdout_df,
        dgp=dgp,
        seed=seed,
        research_signal=[],
        holdout_signal=[],
    )


# ---------------------------------------------------------------------------
# Known Signal Artifact — immutable provenance for the injected signal
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KnownSignalArtifact:
    """Immutable record of a known signal injected into a synthetic world.

    This artifact captures the complete causal chain from DGP to expected
    performance, enabling the system to prove that it can detect the
    phenomenon it governs.

    Includes the full data-generating process specification so that
    results can be attributed to their cause.
    """
    signal_id: str
    world_id: str
    signal_type: str
    signal_strength: float
    noise_std: float
    autocorrelation: float
    noise_distribution: str
    signal_definition: str  # Human-readable description
    information_horizon: str  # "t+1", "t+5", etc.
    expected_direction: str  # "positive", "negative", "state_dependent"
    expected_effect_size: float  # Expected Sharpe contribution
    oracle_strategy: str  # Description of the oracle strategy
    expected_oracle_performance: tuple[float, float]  # (lower_bound, upper_bound)
    expected_agent_performance: tuple[float, float]  # (lower_bound, upper_bound)
    degradation_notes: str = ""

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "world_id": self.world_id,
            "signal_type": self.signal_type,
            "signal_strength": self.signal_strength,
            "noise_std": self.noise_std,
            "autocorrelation": self.autocorrelation,
            "noise_distribution": self.noise_distribution,
            "signal_definition": self.signal_definition,
            "information_horizon": self.information_horizon,
            "expected_direction": self.expected_direction,
            "expected_effect_size": self.expected_effect_size,
            "oracle_strategy": self.oracle_strategy,
            "expected_oracle_performance": list(self.expected_oracle_performance),
            "expected_agent_performance": list(self.expected_agent_performance),
            "degradation_notes": self.degradation_notes,
        }


def generate_known_signal_world(
    world_id: str,
    signal_strength: float = 0.5,
    noise_std: float = 0.02,
    autocorrelation: float = 0.0,
    n_observations: int = 252,
    seed: int = 42,
) -> tuple[SyntheticWorld, KnownSignalArtifact]:
    """Generate a synthetic world with a trivially recoverable signal.

    The signal is directly observable: return[t+1] = alpha * signal[t] + eps[t]
    where signal[t] is a known deterministic function of observable data.

    This makes the signal impossible to miss for an oracle that knows
    the generating process.

    Args:
        world_id: Unique identifier
        signal_strength: Controls alpha (signal coefficient). 0 = pure noise.
        noise_std: Standard deviation of noise component
        autocorrelation: AR(1) coefficient for serial dependence (0 = IID)
        n_observations: Total number of observations
        seed: Random seed

    Returns:
        (SyntheticWorld, KnownSignalArtifact) — the world and the immutable
        signal provenance record.
    """
    rng = np.random.default_rng(seed)

    # Generate dates
    dates = pd.date_range("2024-01-01", periods=n_observations, freq="B")
    research_end_idx = int(n_observations * 0.8)
    research_dates = dates[:research_end_idx]
    holdout_dates = dates[research_end_idx:]

    if signal_strength == 0.0:
        # Pure noise (possibly autocorrelated)
        returns = _generate_autocorrelated_noise(
            n_observations, rng, noise_std, autocorrelation
        )
        signal = np.zeros(n_observations)
        alpha = 0.0
    else:
        # Generate AR(1) returns: returns[t] = ar_coeff * returns[t+1] + eps[t]
        # The autocorrelation of returns = ar_coeff (exactly as declared)
        ar_noise = _generate_autocorrelated_noise(
            n_observations, rng, noise_std, autocorrelation
        )
        returns = ar_noise

        # Generate signal: an observable feature that predicts future returns.
        # The signal is correlated with the INNOVATION (next-period return),
        # NOT added to returns themselves. This preserves the declared
        # autocorrelation of returns while making the signal useful.
        #
        # signal[t] = innovation[t+1] + noise[t]
        # where innovation[t+1] = returns[t+1] - ar_coeff * returns[t]
        # and noise[t] is observation noise scaled by 1/signal_strength.
        #
        # signal_strength controls signal-to-noise:
        # - signal_strength = 1.0: signal = innovation + 1*noise (SNR=1)
        # - signal_strength = 0.5: signal = innovation + 2*noise (SNR=0.5)
        # - signal_strength = 2.0: signal = innovation + 0.5*noise (SNR=2)
        #
        # Correlation(signal, future_return) = sqrt(1 / (1 + (1/signal_strength)^2))
        alpha = signal_strength * 0.1
        
        signal = np.zeros(n_observations)
        for i in range(n_observations - 1):
            # Innovation at t+1
            innovation = returns[i + 1] - autocorrelation * returns[i]
            # Signal is noisy observation of innovation
            # Noise scales inversely with signal_strength
            noise_level = noise_std / max(signal_strength, 0.01)
            signal[i] = innovation + rng.normal(0, noise_level)
        signal[n_observations - 1] = rng.normal(0, noise_std)  # Last value has no future

    # Convert to prices
    prices = 100 * np.exp(np.cumsum(returns))

    research_df = pd.DataFrame({
        "close": prices[:research_end_idx],
        "returns": returns[:research_end_idx],
        "signal": signal[:research_end_idx],
    }, index=research_dates)

    holdout_df = pd.DataFrame({
        "close": prices[research_end_idx:],
        "returns": returns[research_end_idx:],
        "signal": signal[research_end_idx:],
    }, index=holdout_dates)

    dgp = DataGeneratingProcess(
        has_signal=signal_strength > 0,
        signal_type="known_sine" if signal_strength > 0 else "none",
        signal_strength=signal_strength,
        noise_std=noise_std,
        autocorrelation=autocorrelation,
        n_observations=n_observations,
        description=(
            f"Known sine signal: return[t+1] = {alpha:.4f} * sin(2πt/50) + ε, "
            f"autocorrelation={autocorrelation}"
        ),
    )

    world = SyntheticWorld(
        world_id=world_id,
        symbol="KNOWN",
        research_window=(str(research_dates[0].date()), str(research_dates[-1].date())),
        holdout_window=(str(holdout_dates[0].date()), str(holdout_dates[-1].date())),
        research_data=research_df,
        holdout_data=holdout_df,
        dgp=dgp,
        seed=seed,
        research_signal=signal[:research_end_idx].tolist(),
        holdout_signal=signal[research_end_idx:].tolist(),
    )

    if signal_strength == 0.0:
        known_signal = KnownSignalArtifact(
            signal_id=f"signal-{world_id}",
            world_id=world_id,
            signal_type="none",
            signal_strength=0.0,
            noise_std=noise_std,
            autocorrelation=autocorrelation,
            noise_distribution="normal",
            signal_definition="Pure noise: returns are i.i.d. normal with zero mean",
            information_horizon="none",
            expected_direction="none",
            expected_effect_size=0.0,
            oracle_strategy="No oracle possible — no signal exists",
            expected_oracle_performance=(0.0, 0.0),
            expected_agent_performance=(0.0, 0.0),
        )
        return world, known_signal

    # Compute expected oracle performance analytically
    expected_oracle_sharpe = alpha * np.mean(np.abs(signal[:research_end_idx])) / noise_std
    oracle_lower = expected_oracle_sharpe * 0.3
    oracle_upper = expected_oracle_sharpe * 1.5

    known_signal = KnownSignalArtifact(
        signal_id=f"signal-{world_id}",
        world_id=world_id,
        signal_type="known_sine",
        signal_strength=signal_strength,
        noise_std=noise_std,
        autocorrelation=autocorrelation,
        noise_distribution="normal",
        signal_definition=f"return[t+1] = {alpha:.4f} * sin(2πt/50) + ε[t]",
        information_horizon="t+1",
        expected_direction="positive when signal > 0, negative when signal < 0",
        expected_effect_size=expected_oracle_sharpe,
        oracle_strategy="position[t] = sign(signal[t-1]) — go long when sine > 0, short when sine < 0",
        expected_oracle_performance=(oracle_lower, oracle_upper),
        expected_agent_performance=(0.0, float(oracle_upper * 0.8)),
    )

    return world, known_signal


# ---------------------------------------------------------------------------
# Confounder Matrix — runs multiple world types for mechanism attribution
# ---------------------------------------------------------------------------

def run_confounder_matrix(
    signal_strengths: list[float] | None = None,
    autocorrelations: list[float] | None = None,
    seed: int = 42,
    n_observations: int = 252,
    noise_std: float = 0.02,
) -> dict[str, SyntheticWorld]:
    """Generate the full confounder matrix of worlds.

    Creates worlds for all combinations of signal_strength and autocorrelation,
    including null worlds (no signal) and IID worlds (no autocorrelation).

    Returns:
        Dict mapping world_id to SyntheticWorld.
    """
    if signal_strengths is None:
        signal_strengths = [0.0, 0.1, 0.25, 0.5, 1.0]
    if autocorrelations is None:
        autocorrelations = [0.0, 0.3, 0.5]

    worlds = {}

    for signal_strength in signal_strengths:
        for autocorrelation in autocorrelations:
            if signal_strength == 0.0 and autocorrelation == 0.0:
                # Null IID
                world_id = f"null-iid-s{seed}"
                world = generate_null_world(
                    world_id=world_id,
                    noise_std=noise_std,
                    autocorrelation=autocorrelation,
                    seed=seed,
                )
            elif signal_strength == 0.0:
                # Null AR (autocorrelation only, no signal)
                world_id = f"null-ar{autocorrelation}-s{seed}"
                world = generate_null_world(
                    world_id=world_id,
                    noise_std=noise_std,
                    autocorrelation=autocorrelation,
                    seed=seed,
                )
            elif autocorrelation == 0.0:
                # Signal IID (signal only, no autocorrelation)
                world_id = f"signal-s{signal_strength}-iid-s{seed}"
                world = generate_known_signal_world(
                    world_id=world_id,
                    signal_strength=signal_strength,
                    noise_std=noise_std,
                    autocorrelation=autocorrelation,
                    n_observations=n_observations,
                    seed=seed,
                )[0]
            else:
                # Signal + AR (both signal and autocorrelation)
                world_id = f"signal-s{signal_strength}-ar{autocorrelation}-s{seed}"
                world = generate_known_signal_world(
                    world_id=world_id,
                    signal_strength=signal_strength,
                    noise_std=noise_std,
                    autocorrelation=autocorrelation,
                    n_observations=n_observations,
                    seed=seed,
                )[0]

            worlds[world_id] = world

    return worlds
