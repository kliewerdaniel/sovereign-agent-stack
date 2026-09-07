"""Signal Recovery Test — establishes the complete causal chain.

This module implements a diagnostic hierarchy that separates failures of:

0. World validity       — does the synthetic generator produce the declared DGP?
1. Temporal validity    — does the system respect information availability?
2. Signal recoverability — can an oracle recover the injected signal?
3. Agent recoverability — can the actual search process discover it?
4. Statistical discrimination — do DSR/PBO/holdout distinguish signal from null?
5. Governance discrimination — do the gates produce different acceptance rates?
6. Real-world validation  — does behavior survive realistic market data?

The critical insight: before asking whether governance accepts strategies,
we must establish that the experimental substrate can detect the phenomenon
it is supposed to govern.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd

from sas.quant.backtest import BacktestConfig, BacktestEngine
from sas.quant.market import MarketDataProvider, SyntheticDataProvider
from sas.quant.research.experiment import Experiment, ExperimentConfig
from sas.quant.strategy import PositionSizing, SignalDefinition, StrategyArtifact


# ---------------------------------------------------------------------------
# Known Signal Artifact — immutable provenance for the injected signal
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KnownSignalArtifact:
    """Immutable record of a known signal injected into a synthetic world.

    This artifact captures the complete causal chain from DGP to expected
    performance, enabling the system to prove that it can detect the
    phenomenon it governs.
    """
    signal_id: str
    world_id: str
    signal_type: str
    signal_strength: float
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
            "signal_definition": self.signal_definition,
            "information_horizon": self.information_horizon,
            "expected_direction": self.expected_direction,
            "expected_effect_size": self.expected_effect_size,
            "oracle_strategy": self.oracle_strategy,
            "expected_oracle_performance": list(self.expected_oracle_performance),
            "expected_agent_performance": list(self.expected_agent_performance),
            "degradation_notes": self.degradation_notes,
        }


# ---------------------------------------------------------------------------
# Signal Recovery Result — what actually happened
# ---------------------------------------------------------------------------

@dataclass
class SignalRecoveryResult:
    """Result of a signal recovery test."""
    world_id: str
    signal_strength: float
    known_signal: KnownSignalArtifact

    # What the oracle achieved
    oracle_sharpe: float = 0.0
    oracle_total_return: float = 0.0
    oracle_max_drawdown: float = 0.0

    # What the agent achieved
    agent_sharpe: float = 0.0
    agent_total_return: float = 0.0
    agent_max_drawdown: float = 0.0
    agent_incumbent_trial_id: str = ""

    # What random achieved
    random_sharpe: float = 0.0
    random_total_return: float = 0.0

    # What buy-and-hold achieved
    buyhold_sharpe: float = 0.0
    buyhold_total_return: float = 0.0

    # Recovery diagnostics
    oracle_recovered: bool = False
    agent_recovered: bool = False
    signal_detected: bool = False  # oracle > random AND oracle > buyhold

    # Data diagnostics
    research_data_hash: str = ""
    holdout_data_hash: str = ""
    data_materially_different: bool = False

    # Failure localization
    failure_level: Optional[str] = None  # "world", "temporal", "oracle", "agent", "statistics", "governance"
    failure_details: str = ""

    def to_dict(self) -> dict:
        return {
            "world_id": self.world_id,
            "signal_strength": self.signal_strength,
            "known_signal": self.known_signal.to_dict(),
            "oracle_sharpe": self.oracle_sharpe,
            "oracle_total_return": self.oracle_total_return,
            "agent_sharpe": self.agent_sharpe,
            "agent_total_return": self.agent_total_return,
            "random_sharpe": self.random_sharpe,
            "buyhold_sharpe": self.buyhold_sharpe,
            "oracle_recovered": self.oracle_recovered,
            "agent_recovered": self.agent_recovered,
            "signal_detected": self.signal_detected,
            "data_materially_different": self.data_materially_different,
            "failure_level": self.failure_level,
            "failure_details": self.failure_details,
        }


# ---------------------------------------------------------------------------
# Trivial Known-Signal World Generator
# ---------------------------------------------------------------------------

def generate_known_signal_world(
    world_id: str,
    signal_strength: float = 0.5,
    noise_std: float = 0.02,
    n_observations: int = 252,
    seed: int = 42,
) -> tuple[SyntheticWorld, KnownSignalArtifact]:
    """Generate a synthetic world with a trivially recoverable signal.

    The signal is directly observable: return[t+1] = alpha * signal[t] + eps[t]
    where signal[t] is a known deterministic function of observable data.

    This makes the signal impossible to miss for an oracle that knows
    the generating process.
    """
    from sas.quant.experiment.synthetic_worlds import (
        DataGeneratingProcess,
        SyntheticWorld,
    )

    rng = np.random.default_rng(seed)

    # Generate dates
    dates = pd.date_range("2024-01-01", periods=n_observations, freq="B")
    research_end_idx = int(n_observations * 0.8)
    research_dates = dates[:research_end_idx]
    holdout_dates = dates[research_end_idx:]

    if signal_strength == 0.0:
        # Pure noise returns
        returns = rng.normal(0, noise_std, n_observations)
        signal = np.zeros(n_observations)
        alpha = 0.0
    else:
        # Generate signal: a deterministic sine wave with known period
        t = np.arange(n_observations)
        signal = np.sin(2 * np.pi * t / 50)  # 50-day period

        # Generate returns: return[t+1] = alpha * signal[t] + eps[t]
        alpha = signal_strength * 0.1
        returns = np.zeros(n_observations)
        for i in range(1, n_observations):
            returns[i] = alpha * signal[i - 1] + rng.normal(0, noise_std)

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
        n_observations=n_observations,
        description=f"Known sine signal: return[t+1] = {alpha:.4f} * sin(2πt/50) + ε" if signal_strength > 0 else "Pure noise: returns are i.i.d. normal with zero mean",
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
    alpha = signal_strength * 0.1
    expected_oracle_sharpe = alpha * np.mean(np.abs(signal[:research_end_idx])) / noise_std
    oracle_lower = expected_oracle_sharpe * 0.3
    oracle_upper = expected_oracle_sharpe * 1.5

    known_signal = KnownSignalArtifact(
        signal_id=f"signal-{world_id}",
        world_id=world_id,
        signal_type="known_sine",
        signal_strength=signal_strength,
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
# Oracle Strategy — knows the true signal
# ---------------------------------------------------------------------------

def run_oracle_strategy(
    world: SyntheticWorld,
    known_signal: KnownSignalArtifact,
) -> dict:
    """Run the oracle strategy that knows the true signal.

    The oracle uses the known signal to predict next-period returns.
    This establishes the upper bound of what any strategy could achieve.
    """
    research_data = world.research_data
    holdout_data = world.holdout_data

    if known_signal.signal_type == "none":
        # No signal — oracle cannot do better than random
        return {
            "sharpe_ratio": 0.0,
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "note": "No signal exists — oracle cannot recover",
        }

    # Oracle strategy: position[t] = sign(signal[t-1])
    # Compute returns on research window
    signal_values = research_data["signal"].values
    returns = research_data["returns"].values

    # Position at time t is based on signal at time t-1
    positions = np.zeros(len(signal_values) - 1)
    oracle_returns = np.zeros(len(positions))
    for i in range(len(positions)):
        positions[i] = np.sign(signal_values[i])
        oracle_returns[i] = positions[i] * returns[i + 1]

    # Compute Sharpe
    if np.std(oracle_returns) > 0:
        sharpe = float(np.mean(oracle_returns) / np.std(oracle_returns) * np.sqrt(252))
    else:
        sharpe = 0.0

    total_return = float(np.sum(oracle_returns))
    max_dd = _compute_max_drawdown_from_returns(oracle_returns)

    return {
        "sharpe_ratio": sharpe,
        "total_return": total_return,
        "max_drawdown": max_dd,
        "note": f"Oracle using known signal: {known_signal.signal_definition}",
    }


def run_random_strategy(
    world: SyntheticWorld,
    seed: int = 42,
) -> dict:
    """Run a random strategy — baseline for no-skill."""
    research_data = world.research_data
    returns = research_data["returns"].values[1:]

    rng = np.random.default_rng(seed)
    positions = rng.choice([-1, 0, 1], size=len(returns))
    random_returns = positions * returns

    if np.std(random_returns) > 0:
        sharpe = float(np.mean(random_returns) / np.std(random_returns) * np.sqrt(252))
    else:
        sharpe = 0.0

    return {
        "sharpe_ratio": sharpe,
        "total_return": float(np.sum(random_returns)),
        "max_drawdown": _compute_max_drawdown_from_returns(random_returns),
    }


def run_buy_and_hold(world: SyntheticWorld) -> dict:
    """Run buy-and-hold on the research window."""
    research_data = world.research_data
    returns = research_data["returns"].values[1:]

    if np.std(returns) > 0:
        sharpe = float(np.mean(returns) / np.std(returns) * np.sqrt(252))
    else:
        sharpe = 0.0

    return {
        "sharpe_ratio": sharpe,
        "total_return": float(np.sum(returns)),
        "max_drawdown": _compute_max_drawdown_from_returns(returns),
    }


# ---------------------------------------------------------------------------
# Agent Strategy — uses the governed research pipeline
# ---------------------------------------------------------------------------

def run_agent_strategy(
    world: SyntheticWorld,
    known_signal: KnownSignalArtifact,
    trial_budget: int = 20,
    seed: int = 42,
) -> dict:
    """Run the agent search process on the synthetic world.

    This uses the same pipeline as the governed research experiment,
    but with a data provider that serves the synthetic world's data.
    """
    from sas.quant.experiment.synthetic_data_provider import SyntheticWorldProvider
    from sas.quant.orchestration.researcher import Researcher

    # Create experiment config
    config = ExperimentConfig(
        experiment_id=f"signal-recovery-{uuid.uuid4().hex[:8]}",
        world_id=world.world_id,
        trial_budget=trial_budget,
        research_window=world.research_window,
        holdout_window=world.holdout_window,
        model_id="signal-recovery-agent",
        task_id="signal_recovery",
        random_seed=seed,
        max_reflection_rounds=1,
    )

    experiment = Experiment(config)

    # Use the synthetic world provider
    data_provider = SyntheticWorldProvider(world, seed=seed)

    # Run research
    researcher = Researcher(experiment, data_provider=data_provider)
    result = researcher.run_research()

    # Get incumbent
    incumbent = result.incumbent
    if incumbent and incumbent.backtest_result:
        return {
            "sharpe_ratio": incumbent.backtest_result.get("sharpe_ratio", 0.0),
            "total_return": incumbent.backtest_result.get("total_return", 0.0),
            "max_drawdown": incumbent.backtest_result.get("max_drawdown", 0.0),
            "trial_id": incumbent.trial_id,
            "total_trials": result.total_trials,
        }

    return {
        "sharpe_ratio": 0.0,
        "total_return": 0.0,
        "max_drawdown": 0.0,
        "trial_id": "",
        "total_trials": result.total_trials,
    }


# ---------------------------------------------------------------------------
# Signal Recovery Test — the complete diagnostic
# ---------------------------------------------------------------------------

def run_signal_recovery_test(
    signal_strengths: list[float] | None = None,
    seed: int = 42,
    trial_budget: int = 20,
    noise_std: float = 0.02,
    n_observations: int = 252,
) -> list[SignalRecoveryResult]:
    """Run the complete signal recovery diagnostic.

    For each signal strength, this:
    1. Generates a known-signal world
    2. Runs oracle, random, buy-and-hold, and agent strategies
    3. Determines whether the signal was recovered at each level
    4. Localizes any failure

    Returns:
        List of SignalRecoveryResult, one per signal strength.
    """
    if signal_strengths is None:
        signal_strengths = [0.0, 0.1, 0.25, 0.5, 1.0]

    results = []
    for strength in signal_strengths:
        world_id = f"recovery-s{strength}-seed{seed}"
        world, known_signal = generate_known_signal_world(
            world_id=world_id,
            signal_strength=strength,
            noise_std=noise_std,
            n_observations=n_observations,
            seed=seed,
        )

        result = SignalRecoveryResult(
            world_id=world_id,
            signal_strength=strength,
            known_signal=known_signal,
        )

        # Level 0: World validity — verify data is materially different
        _verify_world_validity(result, world)

        # Level 2: Oracle recovery
        oracle_result = run_oracle_strategy(world, known_signal)
        result.oracle_sharpe = oracle_result["sharpe_ratio"]
        result.oracle_total_return = oracle_result["total_return"]
        result.oracle_max_drawdown = oracle_result["max_drawdown"]

        # Level 3: Agent recovery
        agent_result = run_agent_strategy(world, known_signal, trial_budget, seed)
        result.agent_sharpe = agent_result["sharpe_ratio"]
        result.agent_total_return = agent_result["total_return"]
        result.agent_max_drawdown = agent_result["max_drawdown"]
        result.agent_incumbent_trial_id = agent_result.get("trial_id", "")

        # Baselines
        random_result = run_random_strategy(world, seed)
        result.random_sharpe = random_result["sharpe_ratio"]
        result.random_total_return = random_result["total_return"]

        buyhold_result = run_buy_and_hold(world)
        result.buyhold_sharpe = buyhold_result["sharpe_ratio"]
        result.buyhold_total_return = buyhold_result["total_return"]

        # Determine recovery
        result.oracle_recovered = result.oracle_sharpe > max(result.random_sharpe, result.buyhold_sharpe) + 0.1
        result.agent_recovered = result.agent_sharpe > max(result.random_sharpe, result.buyhold_sharpe) + 0.1
        result.signal_detected = result.oracle_recovered  # Oracle is the ground truth

        # Failure localization
        _localize_failure(result, world, known_signal)

        results.append(result)

    return results


def _verify_world_validity(result: SignalRecoveryResult, world: SyntheticWorld) -> None:
    """Verify that the synthetic world produces materially different data."""
    import hashlib

    research_hash = hashlib.md5(
        world.research_data["returns"].values.tobytes()
    ).hexdigest()[:12]
    holdout_hash = hashlib.md5(
        world.holdout_data["returns"].values.tobytes()
    ).hexdigest()[:12]

    result.research_data_hash = research_hash
    result.holdout_data_hash = holdout_hash

    # Check if data has the expected signal characteristics
    if result.signal_strength > 0.0:
        # For signal worlds, check autocorrelation
        autocorr = world.research_data["returns"].autocorr(lag=1)
        # With a known signal, we expect some autocorrelation
        result.data_materially_different = abs(autocorr) > 0.05
    else:
        # For null worlds, check that autocorrelation is low
        autocorr = world.research_data["returns"].autocorr(lag=1)
        result.data_materially_different = abs(autocorr) < 0.1


def _localize_failure(
    result: SignalRecoveryResult,
    world: SyntheticWorld,
    known_signal: KnownSignalArtifact,
) -> None:
    """Determine which level failed."""
    if not result.data_materially_different and result.signal_strength > 0.0:
        result.failure_level = "world"
        result.failure_details = (
            f"World with signal_strength={result.signal_strength} did not produce "
            f"materially different data (autocorr too low). "
            f"The synthetic generator may not be injecting the declared signal."
        )
        return

    if not result.oracle_recovered and result.signal_strength > 0.0:
        result.failure_level = "oracle"
        result.failure_details = (
            f"Oracle failed to recover the known signal. "
            f"Oracle Sharpe={result.oracle_sharpe:.4f}, "
            f"Random={result.random_sharpe:.4f}, "
            f"BuyHold={result.buyhold_sharpe:.4f}. "
            f"This means the signal is not recoverable even with perfect knowledge."
        )
        return

    if not result.agent_recovered and result.signal_strength > 0.0:
        result.failure_level = "agent"
        result.failure_details = (
            f"Agent failed to recover the signal that oracle found. "
            f"Oracle Sharpe={result.oracle_sharpe:.4f}, "
            f"Agent Sharpe={result.agent_sharpe:.4f}. "
            f"The search process cannot discover the known signal."
        )
        return

    if result.signal_strength == 0.0:
        # For null worlds, we WANT the agent to NOT recover
        if result.agent_recovered:
            result.failure_level = "agent_false_positive"
            result.failure_details = (
                f"Agent recovered a signal in a null world. "
                f"Agent Sharpe={result.agent_sharpe:.4f}. "
                f"This is a false positive."
            )
        else:
            result.failure_level = None
            result.failure_details = "Null world correctly produced no recovery."


def _compute_max_drawdown_from_returns(returns: np.ndarray) -> float:
    """Compute max drawdown from a series of returns."""
    cumulative = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    return float(np.min(drawdowns))


# ---------------------------------------------------------------------------
# Report Generator
# ---------------------------------------------------------------------------

def generate_signal_recovery_report(results: list[SignalRecoveryResult]) -> str:
    """Generate a human-readable signal recovery report."""
    lines = [
        "# Signal Recovery Test Report",
        "",
        "## Operating Characteristic",
        "",
        "| Signal Strength | Oracle | Agent | Random | BuyHold | Detected? | Failure Level |",
        "|---|---|---|---|---|---|---|",
    ]

    for r in results:
        detected = "YES" if r.signal_detected else "NO"
        failure = r.failure_level or "none"
        lines.append(
            f"| {r.signal_strength:.2f} | {r.oracle_sharpe:.4f} | {r.agent_sharpe:.4f} | "
            f"{r.random_sharpe:.4f} | {r.buyhold_sharpe:.4f} | {detected} | {failure} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "### Ideal Operating Characteristic",
        "",
        "Oracle and Agent performance should increase with signal strength:",
        "",
        "    1.0 |                         █████",
        "        |                    █████",
        "        |               █████",
        "        |          █████",
        "        |     █████",
        "    0.0 |████",
        "        +----------------------------",
        "          null → weak → moderate → strong",
        "",
        "### Diagnostic Separation",
        "",
        "1. **Invalid worlds**: Oracle does not respond to signal strength",
        "2. **Broken temporal/data plumbing**: Data hashes identical across signal strengths",
        "3. **Agent cannot recover**: Oracle responds but agent does not",
        "4. **Statistics cannot recognize**: Agent recovers but gates reject",
        "5. **Gates cannot discriminate**: Statistics pass but acceptance is flat",
        "",
        "### Failure Localization",
        "",
    ])

    for r in results:
        if r.failure_level:
            lines.append(f"- **{r.world_id}**: {r.failure_details}")

    if not any(r.failure_level for r in results):
        lines.append("- No failures detected. All levels functioning as expected.")

    lines.extend([
        "",
        "---",
        "*Generated by SAS Signal Recovery Test Framework*",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Invariant Tests
# ---------------------------------------------------------------------------

def run_invariant_tests(seed: int = 42) -> dict:
    """Run invariant tests to verify the experimental substrate.

    Returns:
        Dict with test results.
    """
    results = {}

    # Invariant 1: Different signal strengths produce different data
    world_null, _ = generate_known_signal_world("inv-null", 0.0, seed=seed, n_observations=252)
    world_strong, _ = generate_known_signal_world("inv-strong", 1.0, seed=seed, n_observations=252)

    null_returns = world_null.research_data["returns"].values
    strong_returns = world_strong.research_data["returns"].values

    results["different_data"] = not np.allclose(null_returns, strong_returns)
    results["null_autocorr"] = float(world_null.research_data["returns"].autocorr(lag=1))
    results["strong_autocorr"] = float(world_strong.research_data["returns"].autocorr(lag=1))

    # Invariant 2: Oracle responds to signal strength
    _, known_null = generate_known_signal_world("inv-null-oracle", 0.0, seed=seed, n_observations=252)
    _, known_strong = generate_known_signal_world("inv-strong-oracle", 1.0, seed=seed, n_observations=252)

    oracle_null = run_oracle_strategy(world_null, known_null)
    oracle_strong = run_oracle_strategy(world_strong, known_strong)

    results["oracle_null_sharpe"] = oracle_null["sharpe_ratio"]
    results["oracle_strong_sharpe"] = oracle_strong["sharpe_ratio"]
    results["oracle_responds"] = oracle_strong["sharpe_ratio"] > oracle_null["sharpe_ratio"] + 0.1

    # Invariant 3: Same seed + different strength = different data
    world_a, _ = generate_known_signal_world("inv-a", 0.1, seed=42, n_observations=252)
    world_b, _ = generate_known_signal_world("inv-b", 0.5, seed=42, n_observations=252)
    results["same_seed_different_strength"] = not np.allclose(
        world_a.research_data["returns"].values,
        world_b.research_data["returns"].values,
    )

    return results
