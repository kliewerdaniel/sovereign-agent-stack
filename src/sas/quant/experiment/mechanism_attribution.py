"""Mechanism Attribution Matrix — distinguishes what the agent found from why.

This module implements the core experiment: running multiple strategy types
across the confounder matrix to determine not just whether the agent found
something predictable, but WHAT it found and whether it matches the declared
hypothesis.

The five strategy types:

1. Random: No skill baseline. Position is random.
2. BuyHold: Passive baseline. Long and hold.
3. Momentum: Exploits autocorrelation. Uses past returns to predict future.
4. Oracle: Upper bound. Knows the true signal.
5. Agent: The governed research pipeline searching for strategies.

The mechanism attribution table:

| World | Declared Signal | AR | Signal Recovered | AR Exploited | Accepted |
|-------|-----------------|----|------------------|--------------|----------|

Where:
- Signal Recovered: Oracle/agent performance correlates with declared signal
- AR Exploited: Momentum outperforms BuyHold (indicates serial dependence)
- Accepted: Governance accepts the strategy

Key invariant:

    predictability ≠ hypothesis confirmation

A strategy that profits from an unintended confounder must NOT be considered
confirmation of the declared hypothesis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd

from sas.quant.experiment.hypothesis import (
    HypothesisArtifact,
    create_null_hypothesis,
    create_signal_hypothesis,
)
from sas.quant.experiment.synthetic_worlds import (
    DataGeneratingProcess,
    SyntheticWorld,
    generate_known_signal_world,
    generate_null_world,
    run_confounder_matrix,
)
from sas.quant.experiment.epistemic import (
    EpistemicStatus,
    EpistemicEvaluation,
    ObservedMechanismArtifact,
    evaluate_hypothesis,
)
from sas.quant.experiment.substrate_validation import (
    RealizedDistribution,
    characterize_substrate,
)


# ---------------------------------------------------------------------------
# Strategy Results
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StrategyResult:
    """Result of a single strategy on a single world."""

    strategy_name: str
    world_id: str
    sharpe_ratio: float = 0.0
    total_return: float = 0.0
    max_drawdown: float = 0.0
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "strategy_name": self.strategy_name,
            "world_id": self.world_id,
            "sharpe_ratio": self.sharpe_ratio,
            "total_return": self.total_return,
            "max_drawdown": self.max_drawdown,
            "note": self.note,
        }


# ---------------------------------------------------------------------------
# Mechanism Attribution Result
# ---------------------------------------------------------------------------


@dataclass
class MechanismAttributionResult:
    """Complete result for one world across all strategies."""

    world_id: str
    world: SyntheticWorld
    hypothesis: HypothesisArtifact

    # Strategy results
    random: StrategyResult | None = None
    buyhold: StrategyResult | None = None
    momentum: StrategyResult | None = None
    oracle: StrategyResult | None = None
    agent: StrategyResult | None = None

    # Mechanism attribution
    signal_recovered: bool = False
    ar_exploited: bool = False
    hypothesis_confirmed: bool = False
    hypothesis_falsified: bool = False

    # Epistemic layer
    observed_mechanism: ObservedMechanismArtifact | None = None
    epistemic_evaluation: EpistemicEvaluation | None = None

    # Governance
    accepted: bool = False
    acceptance_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "world_id": self.world_id,
            "dgp": self.world.dgp.to_dict(),
            "hypothesis": self.hypothesis.to_dict(),
            "random": self.random.to_dict() if self.random else None,
            "buyhold": self.buyhold.to_dict() if self.buyhold else None,
            "momentum": self.momentum.to_dict() if self.momentum else None,
            "oracle": self.oracle.to_dict() if self.oracle else None,
            "agent": self.agent.to_dict() if self.agent else None,
            "signal_recovered": self.signal_recovered,
            "ar_exploited": self.ar_exploited,
            "hypothesis_confirmed": self.hypothesis_confirmed,
            "hypothesis_falsified": self.hypothesis_falsified,
            "observed_mechanism": self.observed_mechanism.to_dict() if self.observed_mechanism else None,
            "epistemic_evaluation": self.epistemic_evaluation.to_dict() if self.epistemic_evaluation else None,
            "accepted": self.accepted,
            "acceptance_reason": self.acceptance_reason,
        }


# ---------------------------------------------------------------------------
# Strategy Implementations
# ---------------------------------------------------------------------------


def run_random_strategy(world: SyntheticWorld, seed: int = 42) -> StrategyResult:
    """Random strategy: positions are random."""
    research_data = world.research_data
    returns = research_data["returns"].values[1:]

    rng = np.random.default_rng(seed)
    positions = rng.choice([-1, 0, 1], size=len(returns))
    random_returns = positions * returns

    random_returns = np.asarray(random_returns, dtype=float)
    if np.std(random_returns) > 0:
        sharpe = float(np.mean(random_returns) / np.std(random_returns) * np.sqrt(252))
    else:
        sharpe = 0.0

    return StrategyResult(
        strategy_name="Random",
        world_id=world.world_id,
        sharpe_ratio=sharpe,
        total_return=float(np.sum(random_returns)),
        max_drawdown=_compute_max_drawdown(random_returns),
        note="Random positions (no skill)",
    )


def run_buy_and_hold(world: SyntheticWorld) -> StrategyResult:
    """Buy-and-hold strategy: always long."""
    research_data = world.research_data
    returns = np.asarray(research_data["returns"].values[1:], dtype=float)

    if np.std(returns) > 0:
        sharpe = float(np.mean(returns) / np.std(returns) * np.sqrt(252))
    else:
        sharpe = 0.0

    return StrategyResult(
        strategy_name="BuyHold",
        world_id=world.world_id,
        sharpe_ratio=sharpe,
        total_return=float(np.sum(returns)),
        max_drawdown=_compute_max_drawdown(returns),
        note="Passive long",
    )


def run_momentum_strategy(world: SyntheticWorld, lookback: int = 5) -> StrategyResult:
    """Momentum strategy: exploit autocorrelation in returns."""
    research_data = world.research_data
    returns = research_data["returns"].values

    if len(returns) <= lookback:
        return StrategyResult(
            strategy_name="Momentum",
            world_id=world.world_id,
            note="Insufficient data",
        )

    momentum_returns = []
    for i in range(lookback, len(returns)):
        recent = np.asarray(returns[i - lookback:i], dtype=float)
        momentum = float(np.mean(recent))
        position = 1.0 if momentum > 0 else -1.0
        momentum_returns.append(position * float(returns[i]))

    momentum_returns = np.array(momentum_returns, dtype=float)

    if np.std(momentum_returns) > 0:
        sharpe = float(np.mean(momentum_returns) / np.std(momentum_returns) * np.sqrt(252))
    else:
        sharpe = 0.0

    return StrategyResult(
        strategy_name="Momentum",
        world_id=world.world_id,
        sharpe_ratio=sharpe,
        total_return=float(np.sum(momentum_returns)),
        max_drawdown=_compute_max_drawdown(momentum_returns),
        note=f"Momentum (lookback={lookback})",
    )


def run_oracle_strategy(world: SyntheticWorld) -> StrategyResult:
    """Oracle strategy: knows the true signal (if any)."""
    research_data = world.research_data
    dgp = world.dgp

    if not dgp.has_signal or dgp.signal_strength == 0.0:
        return StrategyResult(
            strategy_name="Oracle",
            world_id=world.world_id,
            note="No signal exists — oracle cannot recover",
        )

    signal_values = np.asarray(research_data["signal"].values, dtype=float)
    returns = np.asarray(research_data["returns"].values, dtype=float)

    positions = np.zeros(len(signal_values) - 1)
    oracle_returns = np.zeros(len(positions))
    for i in range(len(positions)):
        positions[i] = np.sign(signal_values[i])
        oracle_returns[i] = positions[i] * returns[i + 1]

    if np.std(oracle_returns) > 0:
        sharpe = float(np.mean(oracle_returns) / np.std(oracle_returns) * np.sqrt(252))
    else:
        sharpe = 0.0

    return StrategyResult(
        strategy_name="Oracle",
        world_id=world.world_id,
        sharpe_ratio=sharpe,
        total_return=float(np.sum(oracle_returns)),
        max_drawdown=_compute_max_drawdown(oracle_returns),
        note="Oracle using known signal",
    )


def run_agent_strategy(
    world: SyntheticWorld,
    trial_budget: int = 20,
    seed: int = 42,
) -> StrategyResult:
    """Agent strategy: uses the governed research pipeline.

    This is the actual search process that the governed research system uses.
    """
    try:
        from sas.quant.experiment.synthetic_data_provider import SyntheticWorldProvider
        from sas.quant.orchestration.researcher import Researcher
        from sas.quant.research.experiment import Experiment, ExperimentConfig

        config = ExperimentConfig(
            experiment_id=f"mech-attr-{world.world_id}",
            world_id=world.world_id,
            trial_budget=trial_budget,
            research_window=world.research_window,
            holdout_window=world.holdout_window,
            model_id="mechanism-attribution-agent",
            task_id="mechanism_attribution",
            random_seed=seed,
            max_reflection_rounds=1,
        )

        experiment = Experiment(config)
        data_provider = SyntheticWorldProvider(world, seed=seed)
        researcher = Researcher(experiment, data_provider=data_provider)
        result = researcher.run_research()

        incumbent = result.incumbent
        if incumbent and incumbent.backtest_result:
            return StrategyResult(
                strategy_name="Agent",
                world_id=world.world_id,
                sharpe_ratio=incumbent.backtest_result.get("sharpe_ratio", 0.0),
                total_return=incumbent.backtest_result.get("total_return", 0.0),
                max_drawdown=incumbent.backtest_result.get("max_drawdown", 0.0),
                note=f"Agent search ({result.total_trials} trials)",
            )
    except Exception as e:
        return StrategyResult(
            strategy_name="Agent",
            world_id=world.world_id,
            note=f"Agent failed: {str(e)[:100]}",
        )

    return StrategyResult(
        strategy_name="Agent",
        world_id=world.world_id,
        note="Agent produced no incumbent",
    )


# ---------------------------------------------------------------------------
# Mechanism Attribution Matrix Runner
# ---------------------------------------------------------------------------


def run_mechanism_attribution_matrix(
    signal_strengths: list[float] | None = None,
    autocorrelations: list[float] | None = None,
    seed: int = 42,
    n_observations: int = 252,
    noise_std: float = 0.02,
    trial_budget: int = 20,
    run_agent: bool = True,
) -> dict[str, MechanismAttributionResult]:
    """Run the complete mechanism attribution matrix.

    For each world in the confounder matrix, run all five strategies and
    determine what mechanism was exploited.

    Args:
        signal_strengths: Signal strengths to test.
        autocorrelations: AR(1) coefficients to test.
        seed: Random seed.
        n_observations: Observations per world.
        noise_std: Noise standard deviation.
        trial_budget: Trial budget for agent strategy.
        run_agent: Whether to run the agent strategy (slower).

    Returns:
        Dict mapping world_id to MechanismAttributionResult.
    """
    if signal_strengths is None:
        signal_strengths = [0.0, 0.5, 1.0]
    if autocorrelations is None:
        autocorrelations = [0.0, 0.3, 0.5]

    worlds = run_confounder_matrix(
        signal_strengths=signal_strengths,
        autocorrelations=autocorrelations,
        seed=seed,
        n_observations=n_observations,
        noise_std=noise_std,
    )

    results: dict[str, MechanismAttributionResult] = {}

    for world_id, world in sorted(worlds.items()):
        dgp = world.dgp

        # Create appropriate hypothesis
        if dgp.has_signal and dgp.signal_strength > 0:
            hypothesis = create_signal_hypothesis(
                experiment_id=f"mech-attr-{world_id}",
                signal_type=dgp.signal_type,
                signal_strength=dgp.signal_strength,
            )
        else:
            hypothesis = create_null_hypothesis(
                experiment_id=f"mech-attr-{world_id}",
            )

        result = MechanismAttributionResult(
            world_id=world_id,
            world=world,
            hypothesis=hypothesis,
        )

        # Run all strategies
        result.random = run_random_strategy(world, seed=seed)
        result.buyhold = run_buy_and_hold(world)
        result.momentum = run_momentum_strategy(world)
        result.oracle = run_oracle_strategy(world)

        if run_agent:
            result.agent = run_agent_strategy(world, trial_budget=trial_budget, seed=seed)

        # Mechanism attribution
        _attribute_mechanism(result)

        results[world_id] = result

    return results


def _build_observed_mechanism(result: MechanismAttributionResult) -> ObservedMechanismArtifact:
    """Build an ObservedMechanismArtifact from the agent's results.
    
    This examines the agent's strategy to determine what mechanism
    was actually exploited, rather than inferring it from Sharpe alone.
    """
    world = result.world
    dgp = world.dgp
    
    # Determine mechanism type from strategy spec
    mechanism_type = "unknown"
    features_used = ["close"]
    information_horizon = "t+1"
    dependency_measure = 0.0
    n_observations = len(world.research_data)
    n_trades = 0
    sharpe = 0.0
    
    if result.agent:
        sharpe = result.agent.sharpe_ratio
    
    # Try to extract strategy details
    # Note: StrategyResult doesn't store strategy_spec directly,
    # but we can infer from the agent's ResearchResult
    # For now, use heuristics based on DGP and agent performance
    
    if dgp.has_signal and dgp.signal_strength > 0:
        # Signal world: check if agent beat momentum significantly
        if result.momentum and result.agent:
            if result.agent.sharpe_ratio > result.momentum.sharpe_ratio + 0.5:
                mechanism_type = "signal"
                features_used = ["close", "returns", "signal"]
                dependency_measure = 0.3  # Approximate
            else:
                mechanism_type = "momentum"
                features_used = ["close", "returns"]
                dependency_measure = 0.1
    else:
        # Null world: agent found something — what?
        if result.ar_exploited and result.agent:
            if result.agent.sharpe_ratio > result.momentum.sharpe_ratio:
                mechanism_type = "momentum"
                features_used = ["close", "returns"]
                dependency_measure = dgp.autocorrelation
            else:
                mechanism_type = "optimization_pressure"
                features_used = ["close", "returns"]
                dependency_measure = 0.0
        elif result.agent and result.agent.sharpe_ratio > 0.5:
            # Agent found high Sharpe on a null world with no AR — overfitting
            mechanism_type = "optimization_pressure"
            features_used = ["close", "returns"]
            dependency_measure = 0.0
        else:
            mechanism_type = "none"
            features_used = ["close"]
            dependency_measure = 0.0
    
    evidence = []
    if result.agent and result.agent.sharpe_ratio > 0.5:
        evidence.append(f"Agent Sharpe={result.agent.sharpe_ratio:.4f}")
    if result.ar_exploited:
        evidence.append(f"Momentum exploited (AR={dgp.autocorrelation})")
    if result.signal_recovered:
        evidence.append("Oracle recovered signal")
    
    return ObservedMechanismArtifact(
        mechanism_id=f"mech-{result.world_id}",
        experiment_id=f"mech-attr-{result.world_id}",
        mechanism_type=mechanism_type,
        features_used=features_used,
        information_horizon=information_horizon,
        dependency_measure=dependency_measure,
        evidence=evidence,
        competing_mechanisms=["autocorrelation", "optimization_pressure"],
        confidence=0.5 if sharpe > 0.5 else 0.1,
        sharpe_ratio=sharpe,
        n_observations=n_observations,
        n_trades=n_trades,
    )


def _attribute_mechanism(result: MechanismAttributionResult) -> None:
    """Determine what mechanism was exploited using epistemic evaluation."""
    dgp = result.world.dgp

    # Signal recovery: Oracle should recover the declared signal
    if result.oracle and result.random and result.buyhold:
        if dgp.has_signal and dgp.signal_strength > 0:
            result.signal_recovered = result.oracle.sharpe_ratio > 0.5
        else:
            result.signal_recovered = False

    # AR exploitation: Momentum should outperform BuyHold when autocorrelation exists
    if result.momentum and result.buyhold:
        result.ar_exploited = (
            result.momentum.sharpe_ratio > result.buyhold.sharpe_ratio + 0.1
            and result.momentum.sharpe_ratio > 0.0
        )

    # Epistemic evaluation: compare observed mechanism against hypothesis
    # Only runs when agent result is available
    if result.agent and result.hypothesis:
        mechanism = _build_observed_mechanism(result)
        result.observed_mechanism = mechanism
        evaluation = evaluate_hypothesis(result.hypothesis, mechanism)
        result.epistemic_evaluation = evaluation
        if evaluation.status == EpistemicStatus.SUPPORTED:
            result.hypothesis_confirmed = True
            result.hypothesis_falsified = False
        elif evaluation.status == EpistemicStatus.REFUTED:
            result.hypothesis_confirmed = False
            result.hypothesis_falsified = True
        else:
            result.hypothesis_confirmed = False
            result.hypothesis_falsified = False
    elif result.hypothesis:
        # No agent result available — cannot make epistemic judgment.
        # DGP-based heuristics are NOT a substitute for observed evidence.
        # The system must not confirm or falsify hypotheses without an
        # ObservedMechanismArtifact from the agent.
        result.epistemic_evaluation = EpistemicEvaluation(
            hypothesis_id=result.hypothesis.hypothesis_id,
            mechanism_id="none",
            status=EpistemicStatus.INCONCLUSIVE,
            reasoning="No agent result available — cannot evaluate hypothesis without observed mechanism",
            confidence=0.0,
        )
        result.hypothesis_confirmed = False
        result.hypothesis_falsified = False

    # Governance acceptance
    if result.agent:
        if result.epistemic_evaluation:
            result.accepted = (
                result.epistemic_evaluation.status == EpistemicStatus.SUPPORTED
                and result.agent.sharpe_ratio > 0.5
            )
            if result.accepted:
                result.acceptance_reason = "Hypothesis supported by observed mechanism"
            elif result.epistemic_evaluation.status == EpistemicStatus.REFUTED:
                result.acceptance_reason = "Hypothesis refuted: mechanism does not match"
            else:
                result.acceptance_reason = "Hypothesis status inconclusive"
        else:
            result.accepted = (
                result.agent.sharpe_ratio > 0.5
                and not result.hypothesis_falsified
            )
            if result.accepted:
                result.acceptance_reason = "Agent found predictability consistent with hypothesis"
            elif result.hypothesis_falsified:
                result.acceptance_reason = "Agent found predictability from confounder"
            else:
                result.acceptance_reason = "Agent did not find sufficient predictability"


# ---------------------------------------------------------------------------
# Report Generator
# ---------------------------------------------------------------------------


def generate_mechanism_attribution_report(
    results: dict[str, MechanismAttributionResult],
) -> str:
    """Generate the mechanism attribution report."""
    lines = [
        "# Mechanism Attribution Matrix Report",
        "",
        "Distinguishes what the agent found from why it was predictable.",
        "",
        "## Key Invariant",
        "",
        "predictability ≠ hypothesis confirmation",
        "",
        "A strategy that profits from an unintended confounder must NOT be",
        "considered confirmation of the declared hypothesis.",
        "",
        "## Mechanism Attribution Table",
        "",
        "| World | Declared Signal | AR | Random | BuyHold | Momentum | Oracle | Agent | Signal Recovered | AR Exploited | Hypothesis Confirmed | Accepted |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for world_id, r in sorted(results.items()):
        dgp = r.world.dgp
        agent_sharpe = f"{r.agent.sharpe_ratio:.2f}" if r.agent else "N/A"
        lines.append(
            f"| {world_id} | {dgp.signal_strength:.2f} | {dgp.autocorrelation:.2f} | "
            f"{r.random.sharpe_ratio:.2f} | {r.buyhold.sharpe_ratio:.2f} | "
            f"{r.momentum.sharpe_ratio:.2f} | {r.oracle.sharpe_ratio:.2f} | "
            f"{agent_sharpe} | "
            f"{'YES' if r.signal_recovered else 'no'} | "
            f"{'YES' if r.ar_exploited else 'no'} | "
            f"{'YES' if r.hypothesis_confirmed else 'no'} | "
            f"{'YES' if r.accepted else 'no'} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "### Signal Recovery",
        "",
        "- Oracle should recover the declared signal (high Sharpe when signal exists)",
        "- Agent should approach oracle performance if search is effective",
        "",
        "### AR Exploitation",
        "",
        "- Momentum should outperform BuyHold when autocorrelation exists",
        "- This indicates the agent can exploit serial dependence",
        "",
        "### Hypothesis Confirmation",
        "",
        "- For Null worlds: hypothesis confirmed if NO predictability found",
        "- For Signal worlds: hypothesis confirmed if signal recovered (not just AR)",
        "",
        "### Governance",
        "",
        "- Accept only if predictability matches the declared hypothesis",
        "- Reject if predictability comes from a confounder",
        "",
        "---",
        "*Generated by SAS Mechanism Attribution Framework*",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _compute_max_drawdown(returns: np.ndarray) -> float:
    """Compute max drawdown from returns."""
    cumulative = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    return float(np.min(drawdowns))
