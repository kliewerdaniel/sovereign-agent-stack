"""Mechanism Investigation — interventions on the evidence-generating process.

This module implements four investigation types that produce evidence artifacts
WITHOUT changing the frozen epistemic API (SUPPORTED/REFUTED/INCONCLUSIVE).

The investigations enrich the ObservedMechanismArtifact with causal evidence:

1. Feature Ablation: Remove the claimed feature, measure performance change.
   Sharpe change → evidence the feature contributed to the observed outcome.
   No change → evidence the strategy did not depend on this feature.

2. Permutation/Placebo: Destroy the claimed temporal relationship while
   preserving marginal statistics. Sharpe persists → evidence of timing-invariant
   structure (e.g., serial dependence). Sharpe drops → evidence the temporal
   ordering carried information the strategy used.

3. Competing Mechanisms: Create worlds where two mechanisms can explain the
   same outcome. Compare feature sensitivity to determine which feature the
   strategy's performance depends on.

4. Temporal Perturbation: Shift the purported causal information while
   preserving superficial statistics. Performance change → evidence the strategy
   is timing-sensitive. No change → evidence the strategy exploits timing-invariant
   structure.

Key architectural principle:
    Evidence may become more precise, diverse, adversarial, and causally
    informative. But evidence does not acquire authority merely because the
    system has accumulated more of it. Authority remains a separate governed
    transition.

The evidence hierarchy:
    Intervention → Observed difference → Evidence about dependency
    → Mechanism evidence → Hypothesis evaluation

NOT:
    Intervention → CAUSALITY = TRUE

Invariant: These investigations produce evidence. They do not produce
new epistemic states. The frozen three-valued logic (SUPPORTED/REFUTED/
INCONCLUSIVE) remains the only authority model.

A conclusion like "feature was causal" is an ontological claim the evidence
cannot support. The evidence supports: "removing the feature materially
changes the observed outcome under the specified experimental conditions."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Any

import numpy as np
import pandas as pd

from sas.quant.experiment.synthetic_worlds import (
    SyntheticWorld,
    generate_signal_world,
    generate_null_world,
)


# ---------------------------------------------------------------------------
# Investigation Result — new evidence artifact
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MechanismInvestigationResult:
    """Result of a mechanism identification investigation.

    This is a new evidence artifact that enriches the ObservedMechanismArtifact
    without changing the frozen epistemic states (SUPPORTED/REFUTED/INCONCLUSIVE).

    Attributes:
        investigation_type: One of "ablation", "permutation", "competing_mechanism",
            "temporal_perturbation".
        mechanism_id: The mechanism being investigated.
        world_id: The world the investigation was run on.
        original_sharpe: Sharpe ratio before perturbation.
        original_total_return: Total return before perturbation.
        perturbed_sharpe: Sharpe ratio after perturbation.
        perturbed_total_return: Total return after perturbation.
        perturbation_description: Human-readable description of what was changed.
        feature_affected: Which feature was perturbed.
        sharpe_drop: original_sharpe - perturbed_sharpe (positive = feature mattered).
        is_robust: True if performance persists despite perturbation (suspicious).
        conclusion: Human-readable conclusion.
        evidence_strength: 0-1, how strongly this supports/refutes the mechanism.
    """

    investigation_type: str
    mechanism_id: str
    world_id: str
    original_sharpe: float = 0.0
    original_total_return: float = 0.0
    perturbed_sharpe: float = 0.0
    perturbed_total_return: float = 0.0
    perturbation_description: str = ""
    feature_affected: str = "returns"
    sharpe_drop: float = 0.0
    is_robust: bool = False
    conclusion: str = ""
    evidence_strength: float = 0.0

    def to_dict(self) -> dict:
        return {
            "investigation_type": self.investigation_type,
            "mechanism_id": self.mechanism_id,
            "world_id": self.world_id,
            "original_sharpe": self.original_sharpe,
            "original_total_return": self.original_total_return,
            "perturbed_sharpe": self.perturbed_sharpe,
            "perturbed_total_return": self.perturbed_total_return,
            "perturbation_description": self.perturbation_description,
            "feature_affected": self.feature_affected,
            "sharpe_drop": self.sharpe_drop,
            "is_robust": self.is_robust,
            "conclusion": self.conclusion,
            "evidence_strength": self.evidence_strength,
        }


# ---------------------------------------------------------------------------
# World Perturbation Helpers
# ---------------------------------------------------------------------------


def _create_perturbed_world(
    world: SyntheticWorld,
    perturbed_research_data: pd.DataFrame,
    perturbation_desc: str,
) -> SyntheticWorld:
    """Create a new SyntheticWorld with modified research data.

    The original world is immutable; this creates a shallow copy with
    perturbed data for investigation purposes.
    """
    return SyntheticWorld(
        world_id=f"{world.world_id}-{perturbation_desc}",
        symbol=world.symbol,
        research_window=world.research_window,
        holdout_window=world.holdout_window,
        research_data=perturbed_research_data,
        holdout_data=world.holdout_data,
        dgp=world.dgp,
        seed=world.seed,
        research_signal=list(world.research_signal),
        holdout_signal=list(world.holdout_signal),
    )


# ---------------------------------------------------------------------------
# Investigation 1: Feature Ablation
# ---------------------------------------------------------------------------


def run_feature_ablation(
    world: SyntheticWorld,
    strategy_fn: Callable[[SyntheticWorld], Any],
    mechanism_id: str,
    feature: str = "returns",
) -> MechanismInvestigationResult:
    """Remove the claimed explanatory feature and measure performance change.

    If the strategy's Sharpe changes when the feature is zeroed out, the
    evidence is consistent with the feature contributing to the observed
    outcome. If Sharpe persists, the evidence is consistent with the
    strategy not depending on this feature.

    Args:
        world: The synthetic world to investigate.
        strategy_fn: A callable that takes a SyntheticWorld and returns a
            StrategyResult-like object with sharpe_ratio and total_return.
        mechanism_id: The mechanism being investigated.
        feature: The feature to ablate (zero out).

    Returns:
        MechanismInvestigationResult with dependency evidence.
    """
    original_result = strategy_fn(world)
    original_sharpe = float(getattr(original_result, "sharpe_ratio", 0.0))
    original_return = float(getattr(original_result, "total_return", 0.0))

    # Create perturbed world with feature zeroed out
    perturbed_data = world.research_data.copy()
    if feature in perturbed_data.columns:
        perturbed_data[feature] = 0.0
    perturbed_world = _create_perturbed_world(world, perturbed_data, f"ablate-{feature}")

    perturbed_result = strategy_fn(perturbed_world)
    perturbed_sharpe = float(getattr(perturbed_result, "sharpe_ratio", 0.0))
    perturbed_return = float(getattr(perturbed_result, "total_return", 0.0))

    sharpe_drop = original_sharpe - perturbed_sharpe
    is_robust = abs(perturbed_sharpe) > 0.2

    # Evidence strength: how much did the feature matter?
    # Large drop → high evidence strength for the mechanism being real
    # Small drop → low evidence (strategy wasn't using the feature)
    evidence_strength = min(abs(sharpe_drop) / max(abs(original_sharpe), 0.5), 1.0)

    if abs(sharpe_drop) > 0.5:
        conclusion = (
            f"Feature ablation: {feature} removed. Sharpe changed "
            f"{original_sharpe:.2f} → {perturbed_sharpe:.2f} (Δ={sharpe_drop:.2f}). "
            f"Evidence consistent with feature contributing to outcome."
        )
    elif abs(sharpe_drop) > 0.1:
        conclusion = (
            f"Feature ablation: {feature} removed. Sharpe changed "
            f"{original_sharpe:.2f} → {perturbed_sharpe:.2f} (Δ={sharpe_drop:.2f}). "
            f"Evidence consistent with partial feature dependence."
        )
    else:
        conclusion = (
            f"Feature ablation: {feature} removed. Sharpe unchanged "
            f"({original_sharpe:.2f} → {perturbed_sharpe:.2f}). "
            f"Evidence consistent with strategy not depending on this feature."
        )

    return MechanismInvestigationResult(
        investigation_type="feature_ablation",
        mechanism_id=mechanism_id,
        world_id=world.world_id,
        original_sharpe=original_sharpe,
        original_total_return=original_return,
        perturbed_sharpe=perturbed_sharpe,
        perturbed_total_return=perturbed_return,
        perturbation_description=f"Zeroed out '{feature}' in research data",
        feature_affected=feature,
        sharpe_drop=sharpe_drop,
        is_robust=is_robust,
        conclusion=conclusion,
        evidence_strength=evidence_strength,
    )


# ---------------------------------------------------------------------------
# Investigation 2: Permutation / Placebo Test
# ---------------------------------------------------------------------------


def run_permutation_test(
    world: SyntheticWorld,
    strategy_fn: Callable[[SyntheticWorld], Any],
    mechanism_id: str,
    feature: str = "returns",
    n_permutations: int = 10,
    seed: int = 42,
) -> MechanismInvestigationResult:
    """Destroy the claimed temporal relationship while preserving marginal stats.

    Shuffles the specified feature to destroy any temporal structure while
    preserving the marginal distribution. If the strategy's Sharpe persists
    on shuffled data, the evidence is consistent with timing-invariant
    structure (e.g., serial dependence). If Sharpe drops, the evidence is
    consistent with the temporal ordering carrying information the strategy used.

    Args:
        world: The synthetic world to investigate.
        strategy_fn: A callable that takes a SyntheticWorld and returns a
            StrategyResult-like object.
        mechanism_id: The mechanism being investigated.
        feature: The feature to permute (shuffle).
        n_permutations: Number of shuffle iterations to average over.
        seed: Random seed for reproducibility.

    Returns:
        MechanismInvestigationResult with temporal-structure evidence.
    """
    original_result = strategy_fn(world)
    original_sharpe = float(getattr(original_result, "sharpe_ratio", 0.0))
    original_return = float(getattr(original_result, "total_return", 0.0))

    rng = np.random.default_rng(seed)
    permuted_sharpes = []
    permuted_returns = []

    for i in range(n_permutations):
        perturbed_data = world.research_data.copy()
        if feature in perturbed_data.columns:
            # Shuffle the feature to destroy temporal structure
            values = np.asarray(perturbed_data[feature].values, dtype=float).copy()
            rng.shuffle(values)
            perturbed_data[feature] = values
        perturbed_world = _create_perturbed_world(
            world, perturbed_data, f"perm-{feature}-{i}"
        )
        perturbed_result = strategy_fn(perturbed_world)
        permuted_sharpes.append(float(getattr(perturbed_result, "sharpe_ratio", 0.0)))
        permuted_returns.append(float(getattr(perturbed_result, "total_return", 0.0)))

    avg_perturbed_sharpe = float(np.mean(permuted_sharpes))
    avg_perturbed_return = float(np.mean(permuted_returns))
    sharpe_drop = original_sharpe - avg_perturbed_sharpe

    # Robustness: if Sharpe persists after shuffling, the strategy is exploiting
    # something other than the claimed temporal relationship
    is_robust = abs(avg_perturbed_sharpe) > 0.2

    # Evidence strength: how much did temporal structure matter?
    evidence_strength = min(abs(sharpe_drop) / max(abs(original_sharpe), 0.5), 1.0)

    if abs(sharpe_drop) > 0.5:
        conclusion = (
            f"Permutation test: {feature} shuffled {n_permutations}x. Sharpe changed "
            f"{original_sharpe:.2f} → {avg_perturbed_sharpe:.2f} (Δ={sharpe_drop:.2f}). "
            f"Evidence consistent with temporal ordering carrying information."
        )
    elif abs(sharpe_drop) > 0.1:
        conclusion = (
            f"Permutation test: {feature} shuffled {n_permutations}x. Sharpe changed "
            f"{original_sharpe:.2f} → {avg_perturbed_sharpe:.2f} (Δ={sharpe_drop:.2f}). "
            f"Evidence consistent with partial temporal dependence."
        )
    else:
        conclusion = (
            f"Permutation test: {feature} shuffled {n_permutations}x. Sharpe persisted "
            f"({original_sharpe:.2f} → {avg_perturbed_sharpe:.2f}). "
            f"Evidence consistent with timing-invariant structure."
        )

    return MechanismInvestigationResult(
        investigation_type="permutation",
        mechanism_id=mechanism_id,
        world_id=world.world_id,
        original_sharpe=original_sharpe,
        original_total_return=original_return,
        perturbed_sharpe=avg_perturbed_sharpe,
        perturbed_total_return=avg_perturbed_return,
        perturbation_description=(
            f"Shuffled '{feature}' {n_permutations}x to destroy temporal structure"
        ),
        feature_affected=feature,
        sharpe_drop=sharpe_drop,
        is_robust=is_robust,
        conclusion=conclusion,
        evidence_strength=evidence_strength,
    )


# ---------------------------------------------------------------------------
# Investigation 3: Competing Mechanisms
# ---------------------------------------------------------------------------


def run_competing_mechanism_test(
    world: SyntheticWorld,
    strategy_fn: Callable[[SyntheticWorld], Any],
    mechanism_id: str,
    signal_feature: str = "signal",
    momentum_feature: str = "returns",
) -> MechanismInvestigationResult:
    """Create worlds where two mechanisms can explain the same outcome.

    Runs two ablation tests — one for the signal feature, one for the
    momentum (autocorrelation) feature. Whichever ablation causes the
    larger Sharpe change provides evidence about which feature the
    strategy's performance depends on.

    This is the critical test for worlds with BOTH signal and AR:
    - If ablating signal causes a bigger drop → evidence strategy uses signal
    - If ablating returns causes a bigger drop → evidence strategy uses AR
    - If both cause similar drops → ambiguous evidence

    Args:
        world: The synthetic world to investigate.
        strategy_fn: A callable that takes a SyntheticWorld and returns a
            StrategyResult-like object.
        mechanism_id: The mechanism being investigated.
        signal_feature: The feature representing the declared signal.
        momentum_feature: The feature representing momentum/autocorrelation.

    Returns:
        MechanismInvestigationResult with competing-mechanism evidence.
    """
    original_result = strategy_fn(world)
    original_sharpe = float(getattr(original_result, "sharpe_ratio", 0.0))
    original_return = float(getattr(original_result, "total_return", 0.0))

    # Ablate signal feature
    signal_ablated_data = world.research_data.copy()
    if signal_feature in signal_ablated_data.columns:
        signal_ablated_data[signal_feature] = 0.0
    signal_ablated_world = _create_perturbed_world(
        world, signal_ablated_data, "ablate-signal"
    )
    signal_ablated_result = strategy_fn(signal_ablated_world)
    signal_ablated_sharpe = float(getattr(signal_ablated_result, "sharpe_ratio", 0.0))

    # Ablate momentum feature
    momentum_ablated_data = world.research_data.copy()
    if momentum_feature in momentum_ablated_data.columns:
        momentum_ablated_data[momentum_feature] = 0.0
    momentum_ablated_world = _create_perturbed_world(
        world, momentum_ablated_data, "ablate-momentum"
    )
    momentum_ablated_result = strategy_fn(momentum_ablated_world)
    momentum_ablated_sharpe = float(getattr(momentum_ablated_result, "sharpe_ratio", 0.0))

    signal_sharpe_drop = original_sharpe - signal_ablated_sharpe
    momentum_sharpe_drop = original_sharpe - momentum_ablated_sharpe

    # Determine which mechanism the strategy actually uses
    if abs(signal_sharpe_drop) > 2 * abs(momentum_sharpe_drop) and signal_sharpe_drop > 0.3:
        conclusion = (
            f"Competing mechanism: Signal ablation changed Sharpe by {signal_sharpe_drop:.2f}, "
            f"momentum ablation by {momentum_sharpe_drop:.2f}. "
            f"Evidence consistent with strategy depending on SIGNAL."
        )
        evidence_strength = min(abs(signal_sharpe_drop) / max(abs(original_sharpe), 0.5), 1.0)
        is_robust = False
        perturbed_sharpe = signal_ablated_sharpe
    elif abs(momentum_sharpe_drop) > 2 * abs(signal_sharpe_drop) and momentum_sharpe_drop > 0.3:
        conclusion = (
            f"Competing mechanism: Momentum ablation changed Sharpe by {momentum_sharpe_drop:.2f}, "
            f"signal ablation by {signal_sharpe_drop:.2f}. "
            f"Evidence consistent with strategy depending on AUTOCORRELATION."
        )
        evidence_strength = min(abs(momentum_sharpe_drop) / max(abs(original_sharpe), 0.5), 1.0)
        is_robust = True
        perturbed_sharpe = momentum_ablated_sharpe
    else:
        conclusion = (
            f"Competing mechanism: Signal ablation changed Sharpe by {signal_sharpe_drop:.2f}, "
            f"momentum ablation by {momentum_sharpe_drop:.2f}. "
            f"Evidence ambiguous — strategy may depend on both or neither."
        )
        evidence_strength = 0.2
        is_robust = False
        perturbed_sharpe = (signal_ablated_sharpe + momentum_ablated_sharpe) / 2

    return MechanismInvestigationResult(
        investigation_type="competing_mechanism",
        mechanism_id=mechanism_id,
        world_id=world.world_id,
        original_sharpe=original_sharpe,
        original_total_return=original_return,
        perturbed_sharpe=perturbed_sharpe,
        perturbed_total_return=0.0,
        perturbation_description=(
            f"Ablated both '{signal_feature}' and '{momentum_feature}' to "
            f"determine which mechanism the strategy exploits"
        ),
        feature_affected=signal_feature if signal_sharpe_drop > momentum_sharpe_drop else momentum_feature,
        sharpe_drop=max(signal_sharpe_drop, momentum_sharpe_drop),
        is_robust=is_robust,
        conclusion=conclusion,
        evidence_strength=evidence_strength,
    )


# ---------------------------------------------------------------------------
# Investigation 4: Temporal Perturbation
# ---------------------------------------------------------------------------


def run_temporal_perturbation(
    world: SyntheticWorld,
    strategy_fn: Callable[[SyntheticWorld], Any],
    mechanism_id: str,
    feature: str = "returns",
    max_shift: int = 5,
    seed: int = 42,
) -> MechanismInvestigationResult:
    """Shift the purported causal information while preserving superficial stats.

    Shifts the feature by k periods (1 to max_shift). If the strategy's
    performance changes, the evidence is consistent with timing sensitivity.
    If performance persists, the evidence is consistent with the strategy
    exploiting timing-invariant structure.

    Args:
        world: The synthetic world to investigate.
        strategy_fn: A callable that takes a SyntheticWorld and returns a
            StrategyResult-like object.
        mechanism_id: The mechanism being investigated.
        feature: The feature to shift.
        max_shift: Maximum number of periods to shift.
        seed: Random seed for reproducibility.

    Returns:
        MechanismInvestigationResult with timing-sensitivity evidence.
    """
    original_result = strategy_fn(world)
    original_sharpe = float(getattr(original_result, "sharpe_ratio", 0.0))
    original_return = float(getattr(original_result, "total_return", 0.0))

    rng = np.random.default_rng(seed)
    shift_sharpes = []
    shift_returns = []

    for shift in range(1, max_shift + 1):
        perturbed_data = world.research_data.copy()
        if feature in perturbed_data.columns:
            values = np.asarray(perturbed_data[feature].values, dtype=float).copy()
            # Shift forward by `shift` periods (use past values as if they were current)
            shifted = np.roll(values, shift)
            # Fill the first `shift` values with random noise to avoid wraparound
            noise_std = float(np.std(values)) if float(np.std(values)) > 0 else 0.01
            shifted[:shift] = rng.normal(0, noise_std, shift)
            perturbed_data[feature] = shifted
        perturbed_world = _create_perturbed_world(
            world, perturbed_data, f"shift-{feature}-{shift}"
        )
        perturbed_result = strategy_fn(perturbed_world)
        shift_sharpes.append(float(getattr(perturbed_result, "sharpe_ratio", 0.0)))
        shift_returns.append(float(getattr(perturbed_result, "total_return", 0.0)))

    avg_shifted_sharpe = float(np.mean(shift_sharpes))
    avg_shifted_return = float(np.mean(shift_returns))
    sharpe_drop = original_sharpe - avg_shifted_sharpe

    # Robustness: if Sharpe persists despite temporal shift, the strategy
    # is exploiting serial dependence (not timing-sensitive mechanism)
    is_robust = abs(avg_shifted_sharpe) > 0.2

    # Evidence strength: how much did timing matter?
    evidence_strength = min(abs(sharpe_drop) / max(abs(original_sharpe), 0.5), 1.0)

    if abs(sharpe_drop) > 0.5:
        conclusion = (
            f"Temporal perturbation: {feature} shifted 1-{max_shift} periods. Sharpe changed "
            f"{original_sharpe:.2f} → {avg_shifted_sharpe:.2f} (Δ={sharpe_drop:.2f}). "
            f"Evidence consistent with timing-sensitive strategy."
        )
    elif abs(sharpe_drop) > 0.1:
        conclusion = (
            f"Temporal perturbation: {feature} shifted 1-{max_shift} periods. Sharpe changed "
            f"{original_sharpe:.2f} → {avg_shifted_sharpe:.2f} (Δ={sharpe_drop:.2f}). "
            f"Evidence consistent with partial timing sensitivity."
        )
    else:
        conclusion = (
            f"Temporal perturbation: {feature} shifted 1-{max_shift} periods. Sharpe persisted "
            f"({original_sharpe:.2f} → {avg_shifted_sharpe:.2f}). "
            f"Evidence consistent with timing-invariant structure."
        )

    return MechanismInvestigationResult(
        investigation_type="temporal_perturbation",
        mechanism_id=mechanism_id,
        world_id=world.world_id,
        original_sharpe=original_sharpe,
        original_total_return=original_return,
        perturbed_sharpe=avg_shifted_sharpe,
        perturbed_total_return=avg_shifted_return,
        perturbation_description=(
            f"Shifted '{feature}' by 1-{max_shift} periods to test timing sensitivity"
        ),
        feature_affected=feature,
        sharpe_drop=sharpe_drop,
        is_robust=is_robust,
        conclusion=conclusion,
        evidence_strength=evidence_strength,
    )


# ---------------------------------------------------------------------------
# Run All Investigations
# ---------------------------------------------------------------------------


def run_all_investigations(
    world: SyntheticWorld,
    strategy_fn: Callable[[SyntheticWorld], Any],
    mechanism_id: str,
    features: list[str] | None = None,
) -> list[MechanismInvestigationResult]:
    """Run all four mechanism investigations and return evidence artifacts.

    Args:
        world: The synthetic world to investigate.
        strategy_fn: A callable that takes a SyntheticWorld and returns a
            StrategyResult-like object.
        mechanism_id: The mechanism being investigated.
        features: Features to test. Defaults to ["returns", "signal"].

    Returns:
        List of MechanismInvestigationResult evidence artifacts.
    """
    if features is None:
        features = ["returns", "signal"]

    investigations = []

    # 1. Feature ablation for each feature
    for feature in features:
        if feature in world.research_data.columns:
            investigations.append(
                run_feature_ablation(world, strategy_fn, mechanism_id, feature)
            )

    # 2. Permutation test on returns (most common confounder)
    if "returns" in world.research_data.columns:
        investigations.append(
            run_permutation_test(world, strategy_fn, mechanism_id, "returns")
        )

    # 3. Competing mechanism test (signal vs momentum)
    if "signal" in world.research_data.columns and "returns" in world.research_data.columns:
        investigations.append(
            run_competing_mechanism_test(world, strategy_fn, mechanism_id)
        )

    # 4. Temporal perturbation on returns
    if "returns" in world.research_data.columns:
        investigations.append(
            run_temporal_perturbation(world, strategy_fn, mechanism_id, "returns")
        )

    return investigations
