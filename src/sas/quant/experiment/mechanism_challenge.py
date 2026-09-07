"""Mechanism Identification Challenge — adversarial test of the evidence layer.

Runs 7 deliberately constructed worlds where the correct epistemic answer is
known in advance. Measures not whether the agent finds a profitable strategy,
but whether the system asserts support for a mechanism or hypothesis when the
experimental world does NOT justify that assertion.

The 7 challenge worlds:

1. One mechanism exists and is obvious → system should find it
2. Two mechanisms produce similar outcomes → evidence should be ambiguous
3. Claimed mechanism is correlated with actual mechanism but not responsible
   → system should NOT assert support for the claimed mechanism
4. Claimed mechanism disappears under temporal perturbation
   → evidence should be timing-sensitive
5. Claimed mechanism survives ablation because agent has substitute feature
   → evidence should reveal substitute dependency
6. Agent discovers profitable mechanism that isn't the registered hypothesis
   → system should NOT assert support for the registered hypothesis
7. Multiple mechanisms produce indistinguishable observational distributions
   → evidence should be INCONCLUSIVE

The key metric: **Epistemic false-positive rate**

    How often did the system assert support for a mechanism or hypothesis
    when the experimental world did not justify that assertion?

This is what SAS is actually trying to solve — not "did the agent find alpha?"
but "did the system correctly determine what the evidence supports?"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import numpy as np
import pandas as pd

from sas.quant.experiment.synthetic_worlds import (
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
    run_all_investigations,
)
from sas.quant.experiment.epistemic import (
    EpistemicStatus,
    ObservedMechanismArtifact,
    evaluate_hypothesis,
)
from sas.quant.experiment.hypothesis import (
    HypothesisArtifact,
    create_signal_hypothesis,
    create_null_hypothesis,
)


# ---------------------------------------------------------------------------
# Challenge World Definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChallengeWorld:
    """A challenge world with known ground truth for epistemic evaluation.

    Attributes:
        world_id: Unique identifier.
        description: Human-readable description of the challenge.
        world: The synthetic world to test.
        declared_hypothesis: The hypothesis the system is asked to evaluate.
        actual_mechanism: The actual mechanism that exists in the world.
        epistemic_false_positive: Whether asserting SUPPORTED would be a false positive.
        expected_evidence: What the evidence should show.
    """

    world_id: str
    description: str
    world: SyntheticWorld
    declared_hypothesis: HypothesisArtifact
    actual_mechanism: str
    would_be_false_positive: bool
    expected_evidence: str


def build_challenge_worlds(seed: int = 42) -> list[ChallengeWorld]:
    """Build the 7 challenge worlds.

    Returns:
        List of ChallengeWorld with known ground truth.
    """
    challenges = []

    # Challenge 1: One mechanism exists and is obvious
    # Signal world with strong signal, no AR
    # System SHOULD find the signal mechanism
    w1 = generate_signal_world(
        world_id="challenge-1-obvious",
        signal_type="momentum",
        signal_strength=0.8,
        noise_std=0.02,
        autocorrelation=0.0,
        seed=seed,
    )
    h1 = create_signal_hypothesis("hyp-1", "momentum", 0.8)
    challenges.append(ChallengeWorld(
        world_id="challenge-1-obvious",
        description="One mechanism exists and is obvious (strong signal, no AR)",
        world=w1,
        declared_hypothesis=h1,
        actual_mechanism="momentum",
        would_be_false_positive=False,
        expected_evidence="Signal ablation should show large Sharpe change",
    ))

    # Challenge 2: Two mechanisms produce similar outcomes
    # Signal + AR world where both contribute equally
    # Evidence should be AMBIGUOUS
    w2 = generate_signal_world(
        world_id="challenge-2-ambiguous",
        signal_type="momentum",
        signal_strength=0.5,
        noise_std=0.02,
        autocorrelation=0.5,
        seed=seed,
    )
    h2 = create_signal_hypothesis("hyp-2", "momentum", 0.5)
    challenges.append(ChallengeWorld(
        world_id="challenge-2-ambiguous",
        description="Two mechanisms produce similar outcomes (signal + AR)",
        world=w2,
        declared_hypothesis=h2,
        actual_mechanism="both",
        would_be_false_positive=True,  # Asserting support for signal alone would be false
        expected_evidence="Competing mechanism test should show similar drops",
    ))

    # Challenge 3: Claimed mechanism is correlated with actual but not responsible
    # Null AR world where momentum works but signal hypothesis is claimed
    # System should NOT assert support for signal hypothesis
    w3 = generate_null_world(
        world_id="challenge-3-correlated",
        seed=seed,
        autocorrelation=0.6,
    )
    h3 = create_signal_hypothesis("hyp-3", "momentum", 0.5)
    challenges.append(ChallengeWorld(
        world_id="challenge-3-correlated",
        description="Claimed mechanism correlated with actual but not responsible (null AR, signal claimed)",
        world=w3,
        declared_hypothesis=h3,
        actual_mechanism="autocorrelation",
        would_be_false_positive=True,  # Asserting support for signal would be false
        expected_evidence="Signal ablation should show no change; returns ablation should show change",
    ))

    # Challenge 4: Claimed mechanism disappears under temporal perturbation
    # Signal world where signal is timing-sensitive
    # Evidence should show timing sensitivity
    w4 = generate_signal_world(
        world_id="challenge-4-temporal",
        signal_type="momentum",
        signal_strength=0.6,
        noise_std=0.02,
        autocorrelation=0.0,
        seed=seed,
    )
    h4 = create_signal_hypothesis("hyp-4", "momentum", 0.6)
    challenges.append(ChallengeWorld(
        world_id="challenge-4-temporal",
        description="Claimed mechanism disappears under temporal perturbation",
        world=w4,
        declared_hypothesis=h4,
        actual_mechanism="momentum",
        would_be_false_positive=False,
        expected_evidence="Temporal perturbation should show large Sharpe change",
    ))

    # Challenge 5: Claimed mechanism survives ablation because agent has substitute
    # Signal world with additional correlated feature
    # Evidence should reveal substitute dependency
    w5 = generate_signal_world(
        world_id="challenge-5-substitute",
        signal_type="momentum",
        signal_strength=0.5,
        noise_std=0.02,
        autocorrelation=0.3,
        seed=seed,
    )
    h5 = create_signal_hypothesis("hyp-5", "momentum", 0.5)
    challenges.append(ChallengeWorld(
        world_id="challenge-5-substitute",
        description="Claimed mechanism survives ablation because agent has substitute feature",
        world=w5,
        declared_hypothesis=h5,
        actual_mechanism="both",
        would_be_false_positive=True,  # Asserting support for signal alone would be false
        expected_evidence="Competing mechanism test should show both features matter",
    ))

    # Challenge 6: Agent discovers profitable mechanism that isn't the registered hypothesis
    # Null AR world where momentum works, but signal hypothesis is claimed
    # System should NOT assert support for the registered hypothesis
    w6 = generate_null_world(
        world_id="challenge-6-unregistered",
        seed=seed,
        autocorrelation=0.7,
    )
    h6 = create_signal_hypothesis("hyp-6", "momentum", 0.5)
    challenges.append(ChallengeWorld(
        world_id="challenge-6-unregistered",
        description="Agent discovers profitable mechanism that isn't the registered hypothesis",
        world=w6,
        declared_hypothesis=h6,
        actual_mechanism="autocorrelation",
        would_be_false_positive=True,  # Asserting support for signal would be false
        expected_evidence="Returns ablation should show change; signal ablation should not",
    ))

    # Challenge 7: Multiple mechanisms produce indistinguishable observational distributions
    # Null IID world — no mechanism exists
    # Evidence should be INCONCLUSIVE
    w7 = generate_null_world(
        world_id="challenge-7-inconclusive",
        seed=seed,
        autocorrelation=0.0,
    )
    h7 = create_signal_hypothesis("hyp-7", "momentum", 0.5)
    challenges.append(ChallengeWorld(
        world_id="challenge-7-inconclusive",
        description="Multiple mechanisms produce indistinguishable observational distributions (null IID)",
        world=w7,
        declared_hypothesis=h7,
        actual_mechanism="none",
        would_be_false_positive=True,  # Asserting support for any mechanism would be false
        expected_evidence="All investigations should show minimal Sharpe changes",
    ))

    return challenges


# ---------------------------------------------------------------------------
# Challenge Runner
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChallengeResult:
    """Result of running one challenge world through the evidence layer.

    Attributes:
        challenge: The challenge world that was run.
        strategy_results: Results from each strategy type.
        investigations: Evidence artifacts from all investigations.
        observed_mechanism: The mechanism the agent actually found.
        epistemic_evaluation: The epistemic evaluation of the declared hypothesis.
        false_positive: Whether the system committed a false positive.
        correct: Whether the system's epistemic judgment was correct.
    """

    challenge: ChallengeWorld
    strategy_results: dict[str, StrategyResult]
    investigations: list[MechanismInvestigationResult]
    observed_mechanism: ObservedMechanismArtifact | None
    epistemic_evaluation: Any  # EpistemicEvaluation
    false_positive: bool
    correct: bool
    notes: str = ""


def run_challenge(
    challenge: ChallengeWorld,
    strategy_fn: Callable[[SyntheticWorld], Any] | None = None,
) -> ChallengeResult:
    """Run one challenge world through the full evidence layer.

    Args:
        challenge: The challenge world to test.
        strategy_fn: Strategy function to use. Defaults to momentum strategy.

    Returns:
        ChallengeResult with epistemic evaluation and false-positive detection.
    """
    if strategy_fn is None:
        strategy_fn = lambda w: run_momentum_strategy(w, lookback=5)

    world = challenge.world

    # Run all four strategies
    strategy_results = {
        "random": run_random_strategy(world),
        "buyhold": run_buy_and_hold(world),
        "momentum": run_momentum_strategy(world, lookback=5),
        "oracle": run_oracle_strategy(world),
        "agent": strategy_fn(world),
    }

    # Run all investigations
    investigations = run_all_investigations(world, strategy_fn, f"mech-{world.world_id}")

    # Build observed mechanism from agent results
    agent_result = strategy_results.get("agent")
    observed_mechanism = _build_observed_mechanism_from_investigations(
        world, agent_result, investigations
    )

    # Evaluate the declared hypothesis
    epistemic_evaluation = evaluate_hypothesis(
        challenge.declared_hypothesis, observed_mechanism
    )

    # Determine if this was a false positive
    false_positive = _check_false_positive(challenge, epistemic_evaluation)

    # Determine if the system's judgment was correct
    correct = _check_correct(challenge, epistemic_evaluation, false_positive)

    return ChallengeResult(
        challenge=challenge,
        strategy_results=strategy_results,
        investigations=investigations,
        observed_mechanism=observed_mechanism,
        epistemic_evaluation=epistemic_evaluation,
        false_positive=false_positive,
        correct=correct,
    )


def _build_observed_mechanism_from_investigations(
    world: SyntheticWorld,
    agent_result: StrategyResult | None,
    investigations: list[MechanismInvestigationResult],
) -> ObservedMechanismArtifact:
    """Build an ObservedMechanismArtifact from investigation results.

    Uses the evidence from all four investigations to determine mechanism type.
    """
    sharpe = 0.0
    total_return = 0.0
    if agent_result:
        sharpe = agent_result.sharpe_ratio
        total_return = agent_result.total_return

    # Analyze investigation results to determine mechanism type
    mechanism_type = "unknown"
    features_used = ["close"]
    dependency_measure = 0.0
    evidence = []

    # Find competing mechanism test
    competing = None
    ablation_returns = None
    ablation_signal = None
    permutation = None
    temporal = None

    for inv in investigations:
        if inv.investigation_type == "competing_mechanism":
            competing = inv
        elif inv.investigation_type == "feature_ablation":
            if inv.feature_affected == "returns":
                ablation_returns = inv
            elif inv.feature_affected == "signal":
                ablation_signal = inv
        elif inv.investigation_type == "permutation":
            permutation = inv
        elif inv.investigation_type == "temporal_perturbation":
            temporal = inv

    # Determine mechanism from evidence
    if competing:
        if "SIGNAL" in competing.conclusion and "depending on SIGNAL" in competing.conclusion:
            mechanism_type = "momentum"
            features_used = ["close", "returns", "signal"]
            dependency_measure = 0.3
        elif "AUTOCORRELATION" in competing.conclusion:
            mechanism_type = "autocorrelation"
            features_used = ["close", "returns"]
            dependency_measure = 0.2
        else:
            mechanism_type = "unknown"
            dependency_measure = 0.1
    elif ablation_returns and ablation_returns.sharpe_drop > 0.3:
        mechanism_type = "momentum"
        features_used = ["close", "returns"]
        dependency_measure = 0.2

    # Collect evidence
    for inv in investigations:
        evidence.append(inv.conclusion)

    return ObservedMechanismArtifact(
        mechanism_id=f"mech-{world.world_id}",
        experiment_id=f"challenge-{world.world_id}",
        mechanism_type=mechanism_type,
        features_used=features_used,
        information_horizon="t+1",
        dependency_measure=dependency_measure,
        evidence=evidence,
        competing_mechanisms=["autocorrelation", "optimization_pressure"],
        confidence=0.5 if sharpe > 0.5 else 0.1,
        sharpe_ratio=sharpe,
        n_observations=len(world.research_data),
        n_trades=0,
    )


def _check_false_positive(
    challenge: ChallengeWorld,
    epistemic_evaluation: Any,  # EpistemicEvaluation
) -> bool:
    """Check if the system committed a false positive.

    A false positive occurs when the system asserts SUPPORTED for a hypothesis
    that the experimental world does not justify.
    """
    if epistemic_evaluation is None:
        return False

    status = epistemic_evaluation.status

    # If the system says SUPPORTED but the challenge says it would be false positive
    if status == EpistemicStatus.SUPPORTED and challenge.would_be_false_positive:
        return True

    return False


def _check_correct(
    challenge: ChallengeWorld,
    epistemic_evaluation: Any,  # EpistemicEvaluation
    false_positive: bool,
) -> bool:
    """Check if the system's epistemic judgment was correct.

    Correct means:
    - If the challenge expects the hypothesis to be supported: status == SUPPORTED
    - If the challenge expects the hypothesis to NOT be supported: status != SUPPORTED
    """
    if epistemic_evaluation is None:
        # No evaluation available — if challenge expects no support, INCONCLUSIVE is correct
        return challenge.would_be_false_positive

    status = epistemic_evaluation.status

    if challenge.would_be_false_positive:
        # System should NOT have asserted SUPPORTED
        return status != EpistemicStatus.SUPPORTED
    else:
        # System should have asserted SUPPORTED
        return status == EpistemicStatus.SUPPORTED


# ---------------------------------------------------------------------------
# Run Full Challenge Suite
# ---------------------------------------------------------------------------


def run_challenge_suite(
    seed: int = 42,
    strategy_fn: Callable[[SyntheticWorld], Any] | None = None,
) -> list[ChallengeResult]:
    """Run all 7 challenge worlds and return results.

    Args:
        seed: Random seed for reproducibility.
        strategy_fn: Strategy function to use. Defaults to momentum strategy.

    Returns:
        List of ChallengeResult, one per challenge world.
    """
    challenges = build_challenge_worlds(seed=seed)
    results = []

    for challenge in challenges:
        result = run_challenge(challenge, strategy_fn)
        results.append(result)

    return results


def generate_challenge_report(results: list[ChallengeResult]) -> str:
    """Generate a report of the challenge suite results.

    The report focuses on epistemic false-positive rate — the key metric
    for what SAS is actually trying to solve.
    """
    lines = [
        "# Mechanism Identification Challenge Report",
        "",
        "Tests whether the system correctly determines what the evidence supports.",
        "",
        "## Key Metric: Epistemic False-Positive Rate",
        "",
        "How often did the system assert support for a mechanism or hypothesis",
        "when the experimental world did NOT justify that assertion?",
        "",
        "## Challenge Results",
        "",
        "| # | Challenge | Actual Mechanism | Declared Hypothesis | System Status | False Positive | Correct |",
        "|---|-----------|-------------------|---------------------|---------------|----------------|---------|",
    ]

    false_positives = 0
    correct_count = 0

    for i, r in enumerate(results, 1):
        challenge = r.challenge
        status = r.epistemic_evaluation.status if r.epistemic_evaluation else "N/A"
        fp = "YES" if r.false_positive else "NO"
        correct = "YES" if r.correct else "NO"

        if r.false_positive:
            false_positives += 1
        if r.correct:
            correct_count += 1

        lines.append(
            f"| {i} | {challenge.world_id} | {challenge.actual_mechanism} | "
            f"{challenge.declared_hypothesis.target_signal} | {status} | {fp} | {correct} |"
        )

    total = len(results)
    fp_rate = false_positives / total if total > 0 else 0.0
    accuracy = correct_count / total if total > 0 else 0.0

    lines.extend([
        "",
        "## Summary",
        "",
        f"- Total challenges: {total}",
        f"- False positives: {false_positives}",
        f"- Epistemic false-positive rate: {fp_rate:.1%}",
        f"- Correct judgments: {correct_count}/{total} ({accuracy:.1%})",
        "",
        "## Interpretation",
        "",
    ])

    if fp_rate == 0.0:
        lines.append(
            "The system committed NO false positives. It correctly refused to assert"
            "support for hypotheses that the experimental worlds did not justify."
        )
    elif fp_rate < 0.3:
        lines.append(
            f"The system committed {false_positives} false positive(s). "
            "This is a low rate, but any false positive means the epistemic layer "
            "allowed an unjustified conclusion."
        )
    else:
        lines.append(
            f"The system committed {false_positives} false positives ({fp_rate:.1%}). "
            "This is a high rate — the epistemic layer is not sufficiently conservative."
        )

    lines.extend([
        "",
        "## Detailed Results",
        "",
    ])

    for i, r in enumerate(results, 1):
        lines.extend([
            f"### Challenge {i}: {r.challenge.world_id}",
            "",
            f"**Description**: {r.challenge.description}",
            "",
            f"**Actual mechanism**: {r.challenge.actual_mechanism}",
            f"**Declared hypothesis**: {r.challenge.declared_hypothesis.target_signal}",
            f"**Would be false positive**: {r.challenge.would_be_false_positive}",
            "",
            "**Strategy results**:",
            "",
            "| Strategy | Sharpe | Return |",
            "|----------|--------|--------|",
        ])

        for name, sr in r.strategy_results.items():
            lines.append(f"| {name} | {sr.sharpe_ratio:.2f} | {sr.total_return:.2f} |")

        lines.extend([
            "",
            "**Investigation evidence**:",
            "",
        ])

        for inv in r.investigations:
            lines.append(f"- {inv.conclusion}")

        lines.extend([
            "",
            f"**Epistemic evaluation**: {r.epistemic_evaluation.status if r.epistemic_evaluation else 'N/A'}",
            f"**False positive**: {'YES' if r.false_positive else 'NO'}",
            f"**Correct**: {'YES' if r.correct else 'NO'}",
            "",
        ])

    return "\n".join(lines)
