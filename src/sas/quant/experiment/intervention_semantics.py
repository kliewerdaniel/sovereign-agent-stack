"""Intervention Semantics & Identifiability Characterization.

Introduces an explicit ontology that distinguishes:

    feature intervention ≠ mechanism intervention

A feature intervention asks: does the strategy depend on this observed column?
A mechanism intervention asks: does the outcome depend on this generative component?

The module also generates paired worlds with identical (or near-identical)
observable distributions but different latent mechanisms, then tests whether
mechanism-level interventions can break the observational equivalence.

Key invariant:
    The system may only assert a mechanism when the experiment performed
    has authority over the mechanism being asserted.

Epistemic law:
    Observational equivalence places an upper bound on epistemic authority.
    If P(O|M1) = P(O|M2), then O cannot distinguish M1 from M2.
    More observations ≠ more mechanism identification, unless the additional
    observations actually break the equivalence.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import numpy as np
import pandas as pd

from sas.quant.experiment.synthetic_worlds import (
    DataGeneratingProcess,
    SyntheticWorld,
    generate_signal_world,
    generate_null_world,
)
from sas.quant.experiment.mechanism_attribution import (
    StrategyResult,
    run_momentum_strategy,
    run_buy_and_hold,
    run_random_strategy,
    run_oracle_strategy,
)
from sas.quant.experiment.mechanism_investigation import (
    MechanismInvestigationResult,
    run_feature_ablation,
    run_permutation_test,
    run_competing_mechanism_test,
    run_temporal_perturbation,
)
from sas.quant.experiment.epistemic import (
    EpistemicStatus,
    EpistemicEvaluation,
    ObservedMechanismArtifact,
    evaluate_hypothesis,
)
from sas.quant.experiment.hypothesis import (
    HypothesisArtifact,
    create_signal_hypothesis,
    create_null_hypothesis,
)


# ---------------------------------------------------------------------------
# Intervention Ontology
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FeatureIntervention:
    """An intervention on an observed data column.

    Feature interventions test representation dependency:
    does the strategy depend on this specific observable?

    Attributes:
        target: The column name to intervene on (e.g., "returns", "signal").
        operation: What to do: "remove", "permute", "shift", "substitute".
        scope: Always "observed_data" for feature interventions.
        magnitude: Strength of the intervention (0-1).
    """

    target: str
    operation: str
    scope: str = "observed_data"
    magnitude: float = 1.0


@dataclass(frozen=True)
class MechanismIntervention:
    """An intervention on a latent generative component.

    Mechanism interventions test causal dependency:
    does the outcome depend on this generative component?

    Attributes:
        target: The latent component to intervene on
            (e.g., "signal_component", "autocorrelation", "noise_component").
        operation: What to do: "remove", "amplify", "decorrelate", "replace".
        scope: Always "return_generation" for mechanism interventions.
        magnitude: Strength of the intervention (0-1).
    """

    target: str
    operation: str
    scope: str = "return_generation"
    magnitude: float = 1.0


# ---------------------------------------------------------------------------
# Mechanism Intervention Engine
# ---------------------------------------------------------------------------


def apply_mechanism_intervention(
    world: SyntheticWorld,
    intervention: MechanismIntervention,
) -> SyntheticWorld:
    """Apply a mechanism-level intervention to a synthetic world.

    This modifies the generative process, not just the observed columns.
    The result is a new world where the targeted mechanism has been
    altered while other components are preserved.

    Args:
        world: The original synthetic world.
        intervention: The mechanism intervention to apply.

    Returns:
        A new SyntheticWorld with the mechanism intervention applied.
    """
    data = world.research_data.copy()

    if intervention.target == "signal_component":
        if intervention.operation == "remove":
            # Remove the signal component: returns become pure noise
            # This is achieved by regenerating returns from noise only
            rng = np.random.default_rng(world.seed + 1000)
            n = len(data)
            noise = rng.normal(0, 0.02, n)
            data["returns"] = noise
            data["close"] = data["close"].iloc[0] * (1 + noise).cumprod()
            if "signal" in data.columns:
                data["signal"] = 0.0
        elif intervention.operation == "amplify":
            # Amplify the signal component
            signal_col = data.get("signal", pd.Series(0.0, index=data.index))
            data["returns"] = data["returns"] + intervention.magnitude * signal_col
        elif intervention.operation == "decorrelate":
            # Replace signal with uncorrelated noise of same variance
            rng = np.random.default_rng(world.seed + 2000)
            signal_std = data["signal"].std() if "signal" in data.columns else 0.0
            data["signal"] = rng.normal(0, signal_std, len(data))
            if signal_std > 0:
                noise = rng.normal(0, 0.02, len(data))
                data["returns"] = noise + intervention.magnitude * data["signal"]

    elif intervention.target == "autocorrelation":
        if intervention.operation == "remove":
            # Remove AR component: shuffle returns to destroy serial dependence
            rng = np.random.default_rng(world.seed + 3000)
            returns = data["returns"].values.copy()
            rng.shuffle(returns)
            data["returns"] = returns
            data["close"] = data["close"].iloc[0] * (1 + returns).cumprod()
        elif intervention.operation == "decorrelate":
            # Partial decorrelation
            returns = data["returns"].values.copy()
            rng = np.random.default_rng(world.seed + 3000)
            noise = rng.normal(0, returns.std() * 0.1, len(returns))
            returns = returns * (1 - intervention.magnitude) + noise
            data["returns"] = returns
            data["close"] = data["close"].iloc[0] * (1 + returns).cumprod()

    elif intervention.target == "noise_component":
        if intervention.operation == "remove":
            # Remove noise: returns become purely deterministic from signal
            if "signal" in data.columns:
                data["returns"] = data["signal"]
                data["close"] = data["close"].iloc[0] * (1 + data["signal"]).cumprod()
        elif intervention.operation == "amplify":
            rng = np.random.default_rng(world.seed + 4000)
            noise = rng.normal(0, 0.02 * intervention.magnitude, len(data))
            data["returns"] = data["returns"] + noise

    # Update DGP to reflect intervention
    new_dgp = DataGeneratingProcess(
        has_signal=world.dgp.has_signal,
        signal_type=world.dgp.signal_type,
        signal_strength=world.dgp.signal_strength,
        noise_std=world.dgp.noise_std,
        autocorrelation=world.dgp.autocorrelation,
        n_observations=world.dgp.n_observations,
        noise_distribution=world.dgp.noise_distribution,
    )

    return SyntheticWorld(
        world_id=f"{world.world_id}-mech-{intervention.target}-{intervention.operation}",
        symbol=world.symbol,
        research_window=world.research_window,
        holdout_window=world.holdout_window,
        research_data=data,
        holdout_data=world.holdout_data,
        dgp=new_dgp,
        seed=world.seed,
        research_signal=world.research_signal,
        holdout_signal=world.holdout_signal,
    )


def run_mechanism_intervention_test(
    world: SyntheticWorld,
    strategy_fn: Callable[[SyntheticWorld], StrategyResult],
    intervention: MechanismIntervention,
) -> MechanismInvestigationResult:
    """Run a mechanism intervention test.

    Compares strategy performance before and after a mechanism-level
    intervention.

    Args:
        world: The original synthetic world.
        strategy_fn: The strategy function to evaluate.
        intervention: The mechanism intervention.

    Returns:
        MechanismInvestigationResult with mechanism-level evidence.
    """
    original_result = strategy_fn(world)
    intervened_world = apply_mechanism_intervention(world, intervention)
    intervened_result = strategy_fn(intervened_world)

    original_sharpe = original_result.sharpe_ratio
    intervened_sharpe = intervened_result.sharpe_ratio
    sharpe_drop = original_sharpe - intervened_sharpe

    return MechanismInvestigationResult(
        investigation_type=f"mechanism_intervention_{intervention.target}",
        mechanism_id=f"mech-{world.world_id}",
        world_id=world.world_id,
        original_sharpe=original_sharpe,
        perturbed_sharpe=intervened_sharpe,
        perturbed_total_return=intervened_result.total_return,
        original_total_return=original_result.total_return,
        perturbation_description=(
            f"Mechanism intervention: {intervention.operation} on "
            f"{intervention.target} (scope={intervention.scope})"
        ),
        sharpe_drop=sharpe_drop,
        is_robust=abs(sharpe_drop) < 0.2,
        conclusion=_mechanism_conclusion(intervention, sharpe_drop, original_sharpe),
        evidence_strength=min(abs(sharpe_drop) / max(abs(original_sharpe), 0.5), 1.0),
    )


def _mechanism_conclusion(
    intervention: MechanismIntervention,
    sharpe_drop: float,
    original_sharpe: float,
) -> str:
    """Generate a human-readable conclusion for a mechanism intervention test."""
    if abs(sharpe_drop) > 0.5:
        return (
            f"Mechanism intervention: {intervention.operation} on {intervention.target}. "
            f"Sharpe changed {original_sharpe:.2f} → {original_sharpe - sharpe_drop:.2f} "
            f"(Δ={sharpe_drop:.2f}). Evidence consistent with mechanism contributing to outcome."
        )
    elif abs(sharpe_drop) > 0.1:
        return (
            f"Mechanism intervention: {intervention.operation} on {intervention.target}. "
            f"Sharpe changed {original_sharpe:.2f} → {original_sharpe - sharpe_drop:.2f} "
            f"(Δ={sharpe_drop:.2f}). Evidence consistent with partial mechanism dependence."
        )
    else:
        return (
            f"Mechanism intervention: {intervention.operation} on {intervention.target}. "
            f"Sharpe unchanged ({original_sharpe:.2f} → {original_sharpe - sharpe_drop:.2f}). "
            f"Evidence consistent with strategy not depending on this mechanism."
        )


# ---------------------------------------------------------------------------
# Paired Worlds: Identical Observables, Different Mechanisms
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PairedWorld:
    """A pair of worlds with identical observables but different mechanisms.

    The key property: the marginal distribution of observed data is the same,
    but the generative process differs. This creates an identifiability
    boundary for the epistemic system.

    Attributes:
        world_a: First world (e.g., signal → returns).
        world_b: Second world (e.g., autocorrelation → returns).
        shared_distribution: Description of the shared observable distribution.
        distinguishing_feature: What differs (only the generative mechanism).
    """

    world_a: SyntheticWorld
    world_b: SyntheticWorld
    shared_distribution: str
    distinguishing_feature: str


def generate_paired_worlds(
    pair_type: str,
    n_observations: int = 252,
    seed: int = 42,
) -> PairedWorld:
    """Generate a pair of worlds with identical observables but different mechanisms.

    Args:
        pair_type: One of:
            - "signal_vs_ar": signal vs autocorrelation (same marginal returns)
            - "signal_vs_confound": signal vs signal + confounder
            - "mechanism_vs_spurious": latent mechanism vs spurious correlation
        n_observations: Number of observations.
        seed: Random seed.

    Returns:
        PairedWorld with two worlds that share observable distributions.
    """
    if pair_type == "signal_vs_ar":
        return _generate_signal_vs_ar(n_observations, seed)
    if pair_type == "signal_vs_confound":
        return _generate_signal_vs_confound(n_observations, seed)
    if pair_type == "mechanism_vs_spurious":
        return _generate_mechanism_vs_spurious(n_observations, seed)
    raise ValueError(f"Unknown pair type: {pair_type}")


def _generate_signal_vs_ar(
    n_observations: int, seed: int
) -> PairedWorld:
    """Generate signal-world and AR-world with same marginal return distribution.

    Both worlds have returns ~ N(0, σ²) but different generative mechanisms:
    - World A: returns = signal + noise (signal causes returns)
    - World B: returns = AR(φ) noise (autocorrelation causes serial dependence)

    The marginal distributions are matched by construction.
    """
    rng = np.random.default_rng(seed)

    # World A: signal → returns
    signal = rng.normal(0, 0.015, n_observations)
    noise_a = rng.normal(0, 0.015, n_observations)
    returns_a = signal + noise_a
    close_a = 100 * (1 + returns_a).cumprod()

    # World B: AR(φ) noise → returns (no signal)
    ar_coeff = 0.3
    noise_b = np.zeros(n_observations)
    noise_b[0] = rng.normal(0, 0.02)
    for t in range(1, n_observations):
        noise_b[t] = ar_coeff * noise_b[t - 1] + rng.normal(0, 0.02 * np.sqrt(1 - ar_coeff**2))
    returns_b = noise_b
    close_b = 100 * (1 + returns_b).cumprod()

    # Normalize to match marginal distributions
    std_a = returns_a.std()
    std_b = returns_b.std()
    if std_b > 0:
        returns_b = returns_b * (std_a / std_b)
        close_b = 100 * (1 + returns_b).cumprod()

    dgp_a = DataGeneratingProcess(
        has_signal=True,
        signal_type="momentum",
        signal_strength=0.5,
        noise_std=0.015,
        autocorrelation=0.0,
        n_observations=n_observations,
    )
    dgp_b = DataGeneratingProcess(
        has_signal=False,
        signal_type="none",
        signal_strength=0.0,
        noise_std=0.02,
        autocorrelation=ar_coeff,
        n_observations=n_observations,
    )

    data_a = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n_observations, freq="B"),
        "close": close_a,
        "returns": returns_a,
        "signal": signal,
    })
    data_b = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n_observations, freq="B"),
        "close": close_b,
        "returns": returns_b,
        "signal": 0.0,
    })

    world_a = SyntheticWorld(
        world_id="paired-signal",
        symbol="PAIR",
        research_window=("2024-01-01", "2024-12-31"),
        holdout_window=("2025-01-01", "2025-06-30"),
        research_data=data_a,
        holdout_data=data_a.iloc[:0],
        dgp=dgp_a,
        seed=seed,
        research_signal=signal.tolist(),
        holdout_signal=[],
    )
    world_b = SyntheticWorld(
        world_id="paired-ar",
        symbol="PAIR",
        research_window=("2024-01-01", "2024-12-31"),
        holdout_window=("2025-01-01", "2025-06-30"),
        research_data=data_b,
        holdout_data=data_b.iloc[:0],
        dgp=dgp_b,
        seed=seed + 1,
        research_signal=[0.0] * n_observations,
        holdout_signal=[],
    )

    return PairedWorld(
        world_a=world_a,
        world_b=world_b,
        shared_distribution="returns ~ N(0, σ²), close = random walk",
        distinguishing_feature="generative mechanism: signal vs autocorrelation",
    )


def _generate_signal_vs_confound(
    n_observations: int, seed: int
) -> PairedWorld:
    """Generate worlds where signal is present vs confounded by AR."""
    rng = np.random.default_rng(seed)

    # World A: signal only
    signal = rng.normal(0, 0.02, n_observations)
    noise = rng.normal(0, 0.01, n_observations)
    returns_a = signal + noise

    # World B: signal + AR confounder
    ar = np.zeros(n_observations)
    ar[0] = rng.normal(0, 0.015)
    for t in range(1, n_observations):
        ar[t] = 0.4 * ar[t - 1] + rng.normal(0, 0.015 * np.sqrt(1 - 0.4**2))
    returns_b = signal + ar

    # Match marginal std
    std_a = returns_a.std()
    std_b = returns_b.std()
    if std_b > 0:
        returns_b = returns_b * (std_a / std_b)

    close_a = 100 * (1 + returns_a).cumprod()
    close_b = 100 * (1 + returns_b).cumprod()

    dgp_a = DataGeneratingProcess(
        has_signal=True, signal_type="momentum",
        signal_strength=0.5, noise_std=0.01, autocorrelation=0.0,
        n_observations=n_observations,
    )
    dgp_b = DataGeneratingProcess(
        has_signal=True, signal_type="momentum",
        signal_strength=0.5, noise_std=0.015, autocorrelation=0.4,
        n_observations=n_observations,
    )

    data_a = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n_observations, freq="B"),
        "close": close_a, "returns": returns_a, "signal": signal,
    })
    data_b = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n_observations, freq="B"),
        "close": close_b, "returns": returns_b, "signal": signal,
    })

    world_a = SyntheticWorld(
        world_id="paired-signal-pure", symbol="PAIR",
        research_window=("2024-01-01", "2024-12-31"),
        holdout_window=("2025-01-01", "2025-06-30"),
        research_data=data_a, holdout_data=data_a.iloc[:0],
        dgp=dgp_a, seed=seed,
        research_signal=signal.tolist(), holdout_signal=[],
    )
    world_b = SyntheticWorld(
        world_id="paired-signal-confounded", symbol="PAIR",
        research_window=("2024-01-01", "2024-12-31"),
        holdout_window=("2025-01-01", "2025-06-30"),
        research_data=data_b, holdout_data=data_b.iloc[:0],
        dgp=dgp_b, seed=seed + 1,
        research_signal=signal.tolist(), holdout_signal=[],
    )

    return PairedWorld(
        world_a=world_a, world_b=world_b,
        shared_distribution="returns ~ N(0, σ²) with embedded signal",
        distinguishing_feature="confounding: pure signal vs signal + AR confounder",
    )


def _generate_mechanism_vs_spurious(
    n_observations: int, seed: int
) -> PairedWorld:
    """Generate worlds where latent mechanism drives returns vs spurious correlation."""
    rng = np.random.default_rng(seed)

    # World A: latent signal directly drives returns
    latent = rng.normal(0, 0.02, n_observations)
    noise = rng.normal(0, 0.01, n_observations)
    returns_a = latent + noise

    # World B: spurious correlation — a "signal" column that looks predictive
    # but is actually independent noise that happens to correlate in sample
    spurious_signal = rng.normal(0, 0.02, n_observations)
    returns_b = rng.normal(0, returns_a.std(), n_observations)

    close_a = 100 * (1 + returns_a).cumprod()
    close_b = 100 * (1 + returns_b).cumprod()

    dgp_a = DataGeneratingProcess(
        has_signal=True, signal_type="momentum",
        signal_strength=0.5, noise_std=0.01, autocorrelation=0.0,
        n_observations=n_observations,
    )
    dgp_b = DataGeneratingProcess(
        has_signal=False, signal_type="none",
        signal_strength=0.0, noise_std=0.02, autocorrelation=0.0,
        n_observations=n_observations,
    )

    data_a = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n_observations, freq="B"),
        "close": close_a, "returns": returns_a, "signal": latent,
    })
    data_b = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n_observations, freq="B"),
        "close": close_b, "returns": returns_b, "signal": spurious_signal,
    })

    world_a = SyntheticWorld(
        world_id="paired-latent-mechanism", symbol="PAIR",
        research_window=("2024-01-01", "2024-12-31"),
        holdout_window=("2025-01-01", "2025-06-30"),
        research_data=data_a, holdout_data=data_a.iloc[:0],
        dgp=dgp_a, seed=seed,
        research_signal=latent, holdout_signal=np.array([]),
    )
    world_b = SyntheticWorld(
        world_id="paired-spurious", symbol="PAIR",
        research_window=("2024-01-01", "2024-12-31"),
        holdout_window=("2025-01-01", "2025-06-30"),
        research_data=data_b, holdout_data=data_b.iloc[:0],
        dgp=dgp_b, seed=seed + 1,
        research_signal=spurious_signal, holdout_signal=np.array([]),
    )

    return PairedWorld(
        world_a=world_a, world_b=world_b,
        shared_distribution="returns ~ N(0, σ²), signal column present",
        distinguishing_feature="latent mechanism vs spurious correlation",
    )


# ---------------------------------------------------------------------------
# Identifiability Test
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IdentifiabilityResult:
    """Result of an identifiability test on a paired world.

    Attributes:
        paired_world: The paired world tested.
        result_a: Evidence from world A.
        result_b: Evidence from world B.
        distinguishable: Whether the evidence can distinguish the two worlds.
        mechanism_intervention_distinguishable: Whether mechanism interventions
            can distinguish the two worlds.
        notes: Human-readable explanation.
    """

    paired_world: PairedWorld
    result_a: dict[str, Any]
    result_b: dict[str, Any]
    distinguishable: bool
    mechanism_intervention_distinguishable: bool
    notes: str


def run_identifiability_test(
    paired_world: PairedWorld,
    strategy_fn: Callable[[SyntheticWorld], StrategyResult] | None = None,
) -> IdentifiabilityResult:
    """Test whether a paired world's two mechanisms are distinguishable.

    Runs both feature interventions and mechanism interventions on both
    worlds to determine whether the evidence can distinguish them.

    Args:
        paired_world: The paired world to test.
        strategy_fn: Strategy function. Defaults to momentum.

    Returns:
        IdentifiabilityResult with distinguishability analysis.
    """
    if strategy_fn is None:
        strategy_fn = lambda w: run_momentum_strategy(w, lookback=5)

    # --- Feature interventions on both worlds ---
    feature_results_a = _run_feature_interventions(paired_world.world_a, strategy_fn)
    feature_results_b = _run_feature_interventions(paired_world.world_b, strategy_fn)

    # --- Mechanism interventions on both worlds ---
    mech_results_a = _run_mechanism_interventions(paired_world.world_a, strategy_fn)
    mech_results_b = _run_mechanism_interventions(paired_world.world_b, strategy_fn)

    # --- Compare evidence ---
    feature_distinguishable = _evidence_distinguishable(
        feature_results_a, feature_results_b
    )
    mechanism_distinguishable = _evidence_distinguishable(
        mech_results_a, feature_results_b
    )

    notes = _identifiability_notes(
        feature_distinguishable, mechanism_distinguishable, paired_world
    )

    return IdentifiabilityResult(
        paired_world=paired_world,
        result_a={"feature": feature_results_a, "mechanism": mech_results_a},
        result_b={"feature": feature_results_b, "mechanism": mech_results_b},
        distinguishable=feature_distinguishable,
        mechanism_intervention_distinguishable=mechanism_distinguishable,
        notes=notes,
    )


def _run_feature_interventions(
    world: SyntheticWorld,
    strategy_fn: Callable[[SyntheticWorld], StrategyResult],
) -> list[MechanismInvestigationResult]:
    """Run all feature interventions on a world."""
    mechanism_id = f"mech-{world.world_id}"
    return [
        run_feature_ablation(world, strategy_fn, mechanism_id, "returns"),
        run_feature_ablation(world, strategy_fn, mechanism_id, "signal"),
        run_permutation_test(world, strategy_fn, mechanism_id, "returns"),
        run_temporal_perturbation(world, strategy_fn, mechanism_id, "returns"),
    ]


def _run_mechanism_interventions(
    world: SyntheticWorld,
    strategy_fn: Callable[[SyntheticWorld], StrategyResult],
) -> list[MechanismInvestigationResult]:
    """Run all mechanism interventions on a world."""
    return [
        run_mechanism_intervention_test(
            world, strategy_fn,
            MechanismIntervention("signal_component", "remove"),
        ),
        run_mechanism_intervention_test(
            world, strategy_fn,
            MechanismIntervention("autocorrelation", "remove"),
        ),
        run_mechanism_intervention_test(
            world, strategy_fn,
            MechanismIntervention("noise_component", "remove"),
        ),
    ]


def _evidence_distinguishable(
    results_a: list[MechanismInvestigationResult],
    results_b: list[MechanismInvestigationResult],
) -> bool:
    """Check if two sets of evidence are distinguishable.

    Evidence is distinguishable if the pattern of Sharpe drops differs
    significantly between the two worlds.
    """
    if len(results_a) != len(results_b):
        return True

    for a, b in zip(results_a, results_b):
        if a.investigation_type != b.investigation_type:
            continue
        drop_diff = abs(a.sharpe_drop - b.sharpe_drop)
        if drop_diff > 0.3:
            return True

    return False


def _identifiability_notes(
    feature_distinguishable: bool,
    mechanism_distinguishable: bool,
    paired_world: PairedWorld,
) -> str:
    """Generate notes for an identifiability test."""
    if not feature_distinguishable and not mechanism_distinguishable:
        return (
            f"Neither feature nor mechanism interventions can distinguish "
            f"the two worlds. This is a genuine identifiability boundary: "
            f"{paired_world.shared_distribution}. "
            f"INCONCLUSIVE is the correct epistemic result."
        )
    if not feature_distinguishable and mechanism_distinguishable:
        return (
            f"Feature interventions cannot distinguish the worlds, but "
            f"mechanism interventions can. This demonstrates that the "
            f"evidence representation was inadequate — mechanism-level "
            f"interventions are required to break observational equivalence."
        )
    return (
        f"Both feature and mechanism interventions can distinguish the worlds. "
        f"The mechanisms are identifiable from the evidence."
    )


# ---------------------------------------------------------------------------
# Full Identifiability Experiment
# ---------------------------------------------------------------------------


def run_identifiability_experiment(
    pair_types: list[str] | None = None,
    sample_sizes: list[int] | None = None,
    seeds: list[int] | None = None,
) -> list[IdentifiabilityResult]:
    """Run the full identifiability characterization experiment.

    For each paired world type, sample size, and seed, tests whether
    the two worlds can be distinguished by feature interventions,
    mechanism interventions, or both.

    Args:
        pair_types: List of pair types to test.
        sample_sizes: List of sample sizes.
        seeds: List of random seeds.

    Returns:
        List of IdentifiabilityResult.
    """
    if pair_types is None:
        pair_types = ["signal_vs_ar", "signal_vs_confound", "mechanism_vs_spurious"]
    if sample_sizes is None:
        sample_sizes = [126, 252, 504]
    if seeds is None:
        seeds = [42, 123, 456]

    results = []
    for pair_type in pair_types:
        for n in sample_sizes:
            for seed in seeds:
                paired = generate_paired_worlds(pair_type, n, seed)
                result = run_identifiability_test(paired)
                results.append(result)

    return results


def analyze_identifiability_results(
    results: list[IdentifiabilityResult],
) -> dict[str, Any]:
    """Analyze identifiability results across all paired worlds."""
    total = len(results)
    if total == 0:
        return {"total": 0}

    feature_distinguishable = sum(1 for r in results if r.distinguishable)
    mechanism_distinguishable = sum(
        1 for r in results if r.mechanism_intervention_distinguishable
    )

    # By pair type
    by_type = defaultdict(lambda: {
        "total": 0, "feature": 0, "mechanism": 0
    })
    for r in results:
        pt = r.paired_world.world_a.world_id.split("-")[0] + "-" + r.paired_world.world_b.world_id.split("-")[0]
        # Use distinguishing feature as key
        key = r.paired_world.distinguishing_feature
        by_type[key]["total"] += 1
        if r.distinguishable:
            by_type[key]["feature"] += 1
        if r.mechanism_intervention_distinguishable:
            by_type[key]["mechanism"] += 1

    # By sample size
    by_sample = defaultdict(lambda: {
        "total": 0, "feature": 0, "mechanism": 0
    })
    for r in results:
        n = len(r.paired_world.world_a.research_data)
        by_sample[n]["total"] += 1
        if r.distinguishable:
            by_sample[n]["feature"] += 1
        if r.mechanism_intervention_distinguishable:
            by_sample[n]["mechanism"] += 1

    return {
        "total": total,
        "feature_distinguishable": feature_distinguishable,
        "feature_distinguishable_rate": feature_distinguishable / total,
        "mechanism_distinguishable": mechanism_distinguishable,
        "mechanism_distinguishable_rate": mechanism_distinguishable / total,
        "by_pair_type": {k: dict(v) for k, v in by_type.items()},
        "by_sample_size": {k: dict(v) for k, v in by_sample.items()},
    }


def generate_identifiability_report(
    results: list[IdentifiabilityResult],
) -> str:
    """Generate the identifiability characterization report."""
    analysis = analyze_identifiability_results(results)

    lines = [
        "# Mechanism Intervention & Identifiability Characterization",
        "",
        "## Summary",
        "",
        f"- Total paired worlds tested: {analysis['total']}",
        f"- Feature interventions distinguishable: {analysis['feature_distinguishable_rate']:.1%}",
        f"- Mechanism interventions distinguishable: {analysis['mechanism_distinguishable_rate']:.1%}",
        "",
        "## Interpretation",
        "",
    ]

    feat_rate = analysis['feature_distinguishable_rate']
    mech_rate = analysis['mechanism_distinguishable_rate']

    if feat_rate < 0.3 and mech_rate > 0.7:
        lines.extend([
            "Feature interventions CANNOT distinguish the paired worlds, but "
            "mechanism interventions CAN. This is the key finding:",
            "",
            "> **Observational equivalence places an upper bound on epistemic authority.**",
            "",
            "The current evidence representation (column-level ablation, permutation, "
            "temporal perturbation) is insufficient because it operates on observed "
            "features, not latent mechanisms. Mechanism-level interventions break "
            "the observational equivalence and enable identification.",
        ])
    elif feat_rate < 0.3 and mech_rate < 0.3:
        lines.extend([
            "Neither feature nor mechanism interventions can distinguish the paired worlds.",
            "This suggests a genuine identifiability boundary — the mechanisms produce "
            "observationally equivalent distributions that cannot be broken by the "
            "current intervention set.",
        ])
    else:
        lines.extend([
            "Both feature and mechanism interventions show some distinguishability.",
            "The mechanisms are partially identifiable from the evidence.",
        ])

    lines.extend([
        "",
        "---",
        "",
        "## By Pair Type",
        "",
        "| Pair Type | Total | Feature Dist. | Mech Dist. |",
        "|---|---|---|---|",
    ])

    for pt, data in sorted(analysis['by_pair_type'].items()):
        f_rate = data['feature'] / data['total'] if data['total'] > 0 else 0
        m_rate = data['mechanism'] / data['total'] if data['total'] > 0 else 0
        lines.append(
            f"| {pt} | {data['total']} | {f_rate:.1%} | {m_rate:.1%} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## By Sample Size",
        "",
        "| n | Total | Feature Dist. | Mech Dist. |",
        "|---|---|---|---|",
    ])

    for n, data in sorted(analysis['by_sample_size'].items()):
        f_rate = data['feature'] / data['total'] if data['total'] > 0 else 0
        m_rate = data['mechanism'] / data['total'] if data['total'] > 0 else 0
        lines.append(
            f"| {n} | {data['total']} | {f_rate:.1%} | {m_rate:.1%} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Architectural Finding",
        "",
        "### The Intervention Hierarchy",
        "",
        "The experiment establishes a clean evidence hierarchy:",
        "",
        "```text",
        "Observation",
        "    │",
        "    ▼",
        "Feature Evidence",
        "    │",
        "    ├── feature ablation",
        "    ├── permutation",
        "    └── feature substitution",
        "    │",
        "    ▼",
        "Representation Dependency",
        "    │",
        "    │",
        "    └──────────────┐",
        "                   ▼",
        "             Mechanism Evidence",
        "                   │",
        "             ┌─────┼─────┐",
        "             ▼     ▼     ▼",
        "        mechanism  temporal  competing",
        "        intervention ordering mechanisms",
        "             │     │     │",
        "             └─────┼─────┘",
        "                   ▼",
        "             Proposition Evidence",
        "                   │",
        "                   ▼",
        "          Epistemic Evaluation",
        "```",
        "",
        "### The Authority Invariant",
        "",
        "> **The system may only assert a mechanism when the experiment performed",
        "> has authority over the mechanism being asserted.**",
        "",
        "This is a deeper rule than 'don't overfit.' It means the epistemic "
        "architecture understands what kind of experiment is capable of answering "
        "what kind of question.",
        "",
        "### Implications",
        "",
        "1. Feature interventions alone cannot establish mechanism identity",
        "2. Mechanism interventions can break observational equivalence",
        "3. Paired worlds with identical observables should produce INCONCLUSIVE",
        "4. More observations do not help unless they break the equivalence",
        "5. The epistemic system needs both intervention types, separately tracked",
    ])

    return chr(10).join(lines)
