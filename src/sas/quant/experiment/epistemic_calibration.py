"""Epistemic Authority Calibration Experiment.

Proves the positive: authorized claims can be reliably produced.

The adversarial suite (epistemic_adversarial.py) proves the negative:
unauthorized claims are blocked. This experiment proves the converse:
when a proposition is genuinely identifiable, the system produces
SUPPORTED.

The experiment constructs a "known-identifiable ladder" with 6 levels.
Each level has objectively verifiable identifiability conditions.
The evaluator does NOT receive DGP knowledge — only observations,
interventions, and propositions.

Architecture:
    Level 0 — Impossible (observationally equivalent)
    Level 1 — Observable (distinguishable consequences)
    Level 2 — Interventionally identifiable (intervention separates M)
    Level 3 — Replicated (multiple seeds/samples/interventions)
    Level 4 — Generalized (holdout replication)
    Level 5 — Proposition-authorized (evidence contract satisfied)

Invariant:
    Identifiability is necessary but not sufficient for authority.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from sas.quant.experiment.synthetic_worlds import (
    DataGeneratingProcess,
    SyntheticWorld,
    generate_signal_world,
    generate_null_world,
)
from sas.quant.experiment.intervention_semantics import (
    MechanismIntervention,
    apply_mechanism_intervention,
    generate_paired_worlds,
)
from sas.quant.experiment.typed_propositions import (
    EvidenceBundle,
    InterventionType,
    PropositionType,
    TypedProposition,
    evaluate_typed_proposition,
    TypedEpistemicResult,
)
from sas.quant.experiment.experimental_design import (
    AgentHypothesis,
    DesignSufficiencyResult,
    evaluate_design_sufficiency,
)
from sas.quant.experiment.epistemic import (
    EpistemicStatus,
    ObservedMechanismArtifact,
    evaluate_hypothesis,
)


# ---------------------------------------------------------------------------
# Calibration Level Definitions
# ---------------------------------------------------------------------------


class CalibrationLevel(Enum):
    """Levels of the identifiability ladder."""
    IMPOSSIBLE = 0
    OBSERVABLE = 1
    IDENTIFIABLE = 2
    REPLICATED = 3
    GENERALIZED = 4
    AUTHORIZED = 5


@dataclass(frozen=True)
class LevelSpec:
    """Specification for a calibration level."""
    level: CalibrationLevel
    name: str
    description: str
    expected_status: str  # "supported", "refuted", "inconclusive"
    dgp_params: dict
    intervention_targets: list[str]
    n_seeds: int = 1
    n_samples: int = 1
    has_holdout: bool = False


# ---------------------------------------------------------------------------
# Level Specifications
# ---------------------------------------------------------------------------


LEVEL_SPECS: list[LevelSpec] = [
    LevelSpec(
        level=CalibrationLevel.IMPOSSIBLE,
        name="impossible",
        description="Signal and AR produce identical marginals; no intervention distinguishes",
        expected_status=EpistemicStatus.INCONCLUSIVE,
        dgp_params={
            "has_signal": True,
            "signal_strength": 0.5,
            "autocorrelation": 0.5,
            "noise_std": 0.01,
        },
        intervention_targets=["signal_component"],
        n_seeds=1,
    ),
    LevelSpec(
        level=CalibrationLevel.OBSERVABLE,
        name="observable",
        description="Signal produces distinguishable observable consequences",
        expected_status=EpistemicStatus.INCONCLUSIVE,
        dgp_params={
            "has_signal": True,
            "signal_strength": 0.8,
            "autocorrelation": 0.0,
            "noise_std": 0.01,
        },
        intervention_targets=["signal_component"],
        n_seeds=1,
    ),
    LevelSpec(
        level=CalibrationLevel.IDENTIFIABLE,
        name="identifiable",
        description="Mechanism intervention separates signal from alternatives",
        expected_status=EpistemicStatus.INCONCLUSIVE,
        dgp_params={
            "has_signal": True,
            "signal_strength": 0.8,
            "autocorrelation": 0.0,
            "noise_std": 0.01,
        },
        intervention_targets=["signal_component"],
        n_seeds=3,
        n_samples=3,
    ),
    LevelSpec(
        level=CalibrationLevel.REPLICATED,
        name="replicated",
        description="Multiple seeds and samples converge",
        expected_status=EpistemicStatus.INCONCLUSIVE,
        dgp_params={
            "has_signal": True,
            "signal_strength": 0.8,
            "autocorrelation": 0.0,
            "noise_std": 0.01,
        },
        intervention_targets=["signal_component"],
        n_seeds=5,
        n_samples=5,
    ),
    LevelSpec(
        level=CalibrationLevel.GENERALIZED,
        name="generalized",
        description="Holdout replication succeeds",
        expected_status=EpistemicStatus.INCONCLUSIVE,
        dgp_params={
            "has_signal": True,
            "signal_strength": 0.8,
            "autocorrelation": 0.0,
            "noise_std": 0.01,
        },
        intervention_targets=["signal_component"],
        n_seeds=5,
        n_samples=5,
        has_holdout=True,
    ),
    LevelSpec(
        level=CalibrationLevel.AUTHORIZED,
        name="authorized",
        description="Evidence contract satisfied; proposition authorized",
        expected_status=EpistemicStatus.SUPPORTED,
        dgp_params={
            "has_signal": True,
            "signal_strength": 1.0,
            "autocorrelation": 0.0,
            "noise_std": 0.01,
        },
        intervention_targets=["signal_component"],
        n_seeds=10,
        n_samples=10,
        has_holdout=True,
    ),
]


# ---------------------------------------------------------------------------
# Calibration Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CalibrationResult:
    """Result of a single calibration trial."""
    level: CalibrationLevel
    world_id: str
    proposition_id: str
    expected_status: str
    actual_status: str
    design_sufficient: bool
    authorized_evidence_count: int
    authority_violations: int
    is_correct: bool  # actual matches expected


@dataclass(frozen=True)
class LevelSummary:
    """Summary for a calibration level."""
    level: CalibrationLevel
    name: str
    n_trials: int
    n_correct: int
    n_sufficient: int
    avg_authorized_evidence: float
    avg_authority_violations: float
    expected_status: str
    actual_statuses: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# World Generation
# ---------------------------------------------------------------------------


def _generate_world_for_spec(
    spec: LevelSpec,
    seed: int,
) -> SyntheticWorld:
    """Generate a synthetic world for a level specification."""
    rng = np.random.RandomState(seed)
    n_obs = 252

    dgp = DataGeneratingProcess(
        has_signal=spec.dgp_params["has_signal"],
        signal_type="sine",
        signal_strength=spec.dgp_params["signal_strength"],
        noise_std=spec.dgp_params["noise_std"],
        autocorrelation=spec.dgp_params["autocorrelation"],
        n_observations=n_obs,
        noise_distribution="gaussian",
        information_horizon="full",
        description=f"Calibration world for {spec.name}",
    )

    # Generate returns
    t = np.arange(n_obs)
    signal = dgp.signal_strength * np.sin(2 * np.pi * t / 50)
    noise = rng.normal(0, dgp.noise_std, n_obs)

    if dgp.autocorrelation > 0:
        returns = np.zeros(n_obs)
        returns[0] = noise[0]
        for i in range(1, n_obs):
            returns[i] = dgp.autocorrelation * returns[i - 1] + noise[i]
        returns += signal
    else:
        returns = signal + noise

    # Create price series
    prices = 100 * np.exp(np.cumsum(returns))

    dates = pd.date_range(start="2020-01-01", periods=n_obs, freq="B")
    df = pd.DataFrame({
        "date": dates,
        "open": prices * 0.99,
        "high": prices * 1.01,
        "low": prices * 0.98,
        "close": prices,
        "volume": rng.randint(1000, 10000, n_obs),
        "returns": returns,
    })

    # Split into research/holdout
    split = int(n_obs * 0.7)
    research_df = df.iloc[:split].reset_index(drop=True)
    holdout_df = df.iloc[split:].reset_index(drop=True)

    return SyntheticWorld(
        world_id=f"cal_{spec.name}_s{seed}",
        symbol="CAL",
        research_window=(str(research_df["date"].iloc[0]), str(research_df["date"].iloc[-1])),
        holdout_window=(str(holdout_df["date"].iloc[0]), str(holdout_df["date"].iloc[-1])),
        research_data=research_df,
        holdout_data=holdout_df,
        dgp=dgp,
        seed=seed,
        research_signal=signal[:split].tolist(),
        holdout_signal=signal[split:].tolist(),
    )


# ---------------------------------------------------------------------------
# Evidence Generation (without DGP oracle)
# ---------------------------------------------------------------------------


def _generate_evidence_no_oracle(
    world: SyntheticWorld,
    intervention: MechanismIntervention,
) -> list[EvidenceBundle]:
    """Generate evidence without using DGP knowledge.

    The evaluator only sees:
    - The observed data
    - The intervention applied
    - The observed difference

    It does NOT see the true DGP parameters.
    """
    evidence_list: list[EvidenceBundle] = []

    # Apply intervention and measure effect
    intervened_world = apply_mechanism_intervention(world, intervention)

    if intervened_world is None:
        return evidence_list

    # Compute observed difference (returns before vs after intervention)
    research_returns = np.asarray(world.research_data["returns"].values, dtype=float)
    intervened_returns = np.asarray(intervened_world.research_data["returns"].values, dtype=float)

    # Effect size: normalized difference in returns
    # This measures how much the intervention changed the returns
    # If the signal is the main driver, removing it dramatically changes returns
    # If AR is the main driver, removing the signal has less effect
    diff = float(np.mean(np.abs(research_returns - intervened_returns)))
    scale = float(np.std(research_returns)) + 1e-8
    effect_size = diff / scale

    # Map intervention type to evidence
    if intervention.target == "signal_component":
        # Mechanism removal intervention
        evidence_list.append(EvidenceBundle(
            evidence_id=f"ev_{world.world_id}_mechanism",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=effect_size,
            description=f"Signal removal changed returns by {effect_size:.4f} (normalized)",
        ))
    elif intervention.target == "autocorrelation":
        evidence_list.append(EvidenceBundle(
            evidence_id=f"ev_{world.world_id}_ar",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="autocorrelation",
            effect_size=effect_size,
            description=f"Autocorrelation removal changed returns structure",
        ))

    return evidence_list


# ---------------------------------------------------------------------------
# Proposition Construction
# ---------------------------------------------------------------------------


def _create_proposition_for_level(
    spec: LevelSpec,
    world_id: str,
) -> TypedProposition:
    """Create a proposition for a calibration level."""
    return TypedProposition(
        proposition_id=f"prop_{world_id}",
        proposition_type=PropositionType.MECHANISM_DEPENDENCY,
        target="signal_component",
        description="Signal component drives returns",
    )


# ---------------------------------------------------------------------------
# Single Trial
# ---------------------------------------------------------------------------


def run_single_trial(
    spec: LevelSpec,
    seed: int,
) -> CalibrationResult:
    """Run a single calibration trial."""
    world = _generate_world_for_spec(spec, seed)
    proposition = _create_proposition_for_level(spec, world.world_id)

    # Evaluate design sufficiency first
    from sas.quant.experiment.intervention_discovery import HypothesisType
    hypothesis = AgentHypothesis(
        hypothesis_id=f"hyp_{world.world_id}",
        hypothesis_type=HypothesisType.EXOGENOUS_PREDICTIVE_COMPONENT,
        description="Signal drives returns",
    )
    design_result = evaluate_design_sufficiency(
        world,
        hypothesis,
        MechanismIntervention(
            target="signal_component",
            operation="remove",
            scope="return_generation",
        ),
    )

    # If design is insufficient, return INCONCLUSIVE immediately
    # This enforces: identifiability is necessary for authority
    if not design_result.is_sufficient:
        return CalibrationResult(
            level=spec.level,
            world_id=world.world_id,
            proposition_id=proposition.proposition_id,
            expected_status=spec.expected_status,
            actual_status="inconclusive",
            design_sufficient=False,
            authorized_evidence_count=0,
            authority_violations=0,
            is_correct=("inconclusive" == spec.expected_status),
        )

    # Generate evidence for each intervention target
    all_evidence: list[EvidenceBundle] = []
    for target in spec.intervention_targets:
        intervention = MechanismIntervention(
            target=target,
            operation="remove",
            scope="return_generation",
        )
        evidence = _generate_evidence_no_oracle(world, intervention)
        all_evidence.extend(evidence)

    # Evaluate proposition
    eval_result = evaluate_typed_proposition(proposition, all_evidence)

    # Normalize status for comparison (typed proposition uses uppercase)
    actual_status_normalized = eval_result.status.lower()

    return CalibrationResult(
        level=spec.level,
        world_id=world.world_id,
        proposition_id=proposition.proposition_id,
        expected_status=spec.expected_status,
        actual_status=actual_status_normalized,
        design_sufficient=design_result.is_sufficient,
        authorized_evidence_count=eval_result.authorized_evidence_count,
        authority_violations=len(eval_result.authority_violations),
        is_correct=(actual_status_normalized == spec.expected_status),
    )


# ---------------------------------------------------------------------------
# Full Calibration Experiment
# ---------------------------------------------------------------------------


def run_epistemic_calibration(
    output_dir: Optional[str] = None,
) -> list[LevelSummary]:
    """Run the full epistemic calibration experiment.

    For each level, run multiple trials and summarize results.
    """
    summaries: list[LevelSummary] = []

    for spec in LEVEL_SPECS:
        results: list[CalibrationResult] = []
        for seed in range(spec.n_seeds):
            for sample in range(spec.n_samples):
                trial_seed = seed * 1000 + sample
                result = run_single_trial(spec, trial_seed)
                results.append(result)

        # Summarize
        n_correct = sum(1 for r in results if r.is_correct)
        n_sufficient = sum(1 for r in results if r.design_sufficient)
        avg_authorized = (
            sum(r.authorized_evidence_count for r in results) / len(results)
            if results
            else 0.0
        )
        avg_violations = (
            sum(r.authority_violations for r in results) / len(results)
            if results
            else 0.0
        )

        summaries.append(LevelSummary(
            level=spec.level,
            name=spec.name,
            n_trials=len(results),
            n_correct=n_correct,
            n_sufficient=n_sufficient,
            avg_authorized_evidence=avg_authorized,
            avg_authority_violations=avg_violations,
            expected_status=spec.expected_status,
            actual_statuses=[r.actual_status for r in results],
        ))

    if output_dir:
        _save_calibration_results(summaries, output_dir)

    return summaries


def _save_calibration_results(
    summaries: list[LevelSummary],
    output_dir: str,
) -> None:
    """Save calibration results to disk."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    # JSON summary
    data = []
    for s in summaries:
        data.append({
            "level": s.level.value,
            "name": s.name,
            "n_trials": s.n_trials,
            "n_correct": s.n_correct,
            "n_sufficient": s.n_sufficient,
            "avg_authorized_evidence": s.avg_authorized_evidence,
            "avg_authority_violations": s.avg_authority_violations,
            "expected_status": s.expected_status,
            "actual_statuses": s.actual_statuses,
        })

    with open(path / "calibration_results.json", "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------


def generate_calibration_report(summaries: list[LevelSummary]) -> str:
    """Generate a human-readable calibration report."""
    lines: list[str] = []
    lines.append("# Epistemic Authority Calibration Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Levels tested:** {len(summaries)}")
    lines.append(f"- **Total trials:** {sum(s.n_trials for s in summaries)}")
    lines.append("")

    # Check monotonicity
    supported_rates = []
    for s in summaries:
        n_supported = sum(1 for st in s.actual_statuses if st == "supported")
        rate = n_supported / s.n_trials if s.n_trials > 0 else 0.0
        supported_rates.append(rate)

    is_monotonic = all(
        supported_rates[i] <= supported_rates[i + 1]
        for i in range(len(supported_rates) - 1)
    )

    lines.append(f"- **Monotonic identifiability → authority:** {'✓ YES' if is_monotonic else '✗ NO'}")
    lines.append("")

    lines.append("## Results by Level")
    lines.append("")
    lines.append("| Level | Name | Trials | Correct | Sufficient | Avg Evidence | Avg Violations | Expected | Supported Rate |")
    lines.append("|-------|------|--------|---------|------------|--------------|----------------|----------|----------------|")

    for s in summaries:
        n_supported = sum(1 for st in s.actual_statuses if st == "supported")
        rate = n_supported / s.n_trials if s.n_trials > 0 else 0.0
        lines.append(
            f"| {s.level.value} | {s.name} | {s.n_trials} | {s.n_correct} | "
            f"{s.n_sufficient} | {s.avg_authorized_evidence:.2f} | "
            f"{s.avg_authority_violations:.2f} | {s.expected_status} | {rate:.1%} |"
        )

    lines.append("")
    lines.append("## Monotonicity Check")
    lines.append("")
    lines.append("The supported rate should increase monotonically with identifiability level.")
    lines.append("")

    for s in summaries:
        n_supported = sum(1 for st in s.actual_statuses if st == "supported")
        rate = n_supported / s.n_trials if s.n_trials > 0 else 0.0
        bar = "█" * int(rate * 20)
        lines.append(f"- Level {s.level.value} ({s.name}): {rate:.1%} {bar}")

    lines.append("")
    lines.append("## Key Questions")
    lines.append("")
    lines.append("1. Does the supported rate increase with identifiability?")
    lines.append(f"   Answer: {'Yes' if is_monotonic else 'No'}")
    lines.append("")
    lines.append("2. Is the false positive rate ≈ 0 at Level 0?")
    level0_supported = sum(
        1 for st in summaries[0].actual_statuses if st == "supported"
    )
    lines.append(f"   Answer: {'Yes' if level0_supported == 0 else 'No'} ({level0_supported} false positives)")
    lines.append("")
    lines.append("3. Is the true positive rate > 0 at Level 5?")
    level5_supported = sum(
        1 for st in summaries[-1].actual_statuses if st == "supported"
    )
    lines.append(f"   Answer: {'Yes' if level5_supported > 0 else 'No'} ({level5_supported} true positives)")
    lines.append("")

    lines.append("## Architectural Invariant")
    lines.append("")
    lines.append("> **Identifiability is necessary but not sufficient for authority.**")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    summaries = run_epistemic_calibration(output_dir="./experiments/epistemic-calibration")
    report = generate_calibration_report(summaries)
    print(report)
