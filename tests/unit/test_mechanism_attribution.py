"""Tests for substrate validation, hypothesis, and mechanism attribution.

Adversarial epistemic tests: these verify that the system does NOT
allow Sharpe, predictability, or DGP knowledge to substitute for
actual observed mechanism evidence.

Key invariants tested:

    high Sharpe ≠ predictable mechanism
    predictable mechanism ≠ identified mechanism
    identified mechanism ≠ hypothesis support
    hypothesis support ≠ governance approval
    signal_not_observed ≠> hypothesis refuted
    INCONCLUSIVE is first-class (not collapsed)
"""

import numpy as np
import pytest

from sas.quant.experiment.epistemic import (
    EpistemicStatus,
    EpistemicEvaluation,
    ObservedMechanismArtifact,
    evaluate_hypothesis,
)
from sas.quant.experiment.hypothesis import (
    HypothesisArtifact,
    create_null_hypothesis,
    create_signal_hypothesis,
)
from sas.quant.experiment.mechanism_attribution import (
    MechanismAttributionResult,
    StrategyResult,
    _attribute_mechanism,
    run_buy_and_hold,
    run_mechanism_attribution_matrix,
    run_momentum_strategy,
    run_oracle_strategy,
    run_random_strategy,
)
from sas.quant.experiment.synthetic_worlds import (
    generate_known_signal_world,
    generate_null_world,
)
from sas.quant.experiment.substrate_validation import (
    RealizedDistribution,
    characterize_substrate,
)


# ---------------------------------------------------------------------------
# Substrate Validation Tests (unchanged — these test the DGP itself)
# ---------------------------------------------------------------------------


class TestSubstrateValidation:
    def test_characterize_substrate_runs(self):
        dists = characterize_substrate(
            signal_strengths=[0.0, 0.5],
            autocorrelations=[0.0, 0.3],
            n_worlds=20,
            n_observations=252,
        )
        assert len(dists) == 4

    def test_null_iid_centered_at_zero(self):
        dists = characterize_substrate(
            signal_strengths=[0.0],
            autocorrelations=[0.0],
            n_worlds=100,
            n_observations=252,
        )
        d = dists["s0.0-ar0.0"]
        assert abs(d.mean) < 0.05
        assert d.ci_lower < 0 < d.ci_upper

    def test_ar_0_3_approximate(self):
        dists = characterize_substrate(
            signal_strengths=[0.0],
            autocorrelations=[0.3],
            n_worlds=100,
            n_observations=252,
        )
        d = dists["s0.0-ar0.3"]
        assert 0.2 < d.mean < 0.4

    def test_ar_0_5_approximate(self):
        dists = characterize_substrate(
            signal_strengths=[0.0],
            autocorrelations=[0.5],
            n_worlds=100,
            n_observations=252,
        )
        d = dists["s0.0-ar0.5"]
        assert 0.4 < d.mean < 0.6

    def test_signal_does_not_dilute_autocorrelation(self):
        """Signal should not significantly change return autocorrelation."""
        dists_null = characterize_substrate(
            signal_strengths=[0.0],
            autocorrelations=[0.3],
            n_worlds=50,
            n_observations=252,
        )
        dists_signal = characterize_substrate(
            signal_strengths=[0.5],
            autocorrelations=[0.3],
            n_worlds=50,
            n_observations=252,
        )
        d_null = dists_null["s0.0-ar0.3"]
        d_signal = dists_signal["s0.5-ar0.3"]
        # Means should be within 0.1 of each other
        assert abs(d_null.mean - d_signal.mean) < 0.1

    def test_realized_distribution_contains(self):
        dists = characterize_substrate(
            signal_strengths=[0.0],
            autocorrelations=[0.0],
            n_worlds=100,
            n_observations=252,
        )
        d = dists["s0.0-ar0.0"]
        assert d.contains(d.mean)
        assert not d.contains(10.0)


# ---------------------------------------------------------------------------
# Hypothesis Tests (unchanged — these test hypothesis creation/comparison)
# ---------------------------------------------------------------------------


class TestHypothesisArtifact:
    def test_null_hypothesis_creation(self):
        h = create_null_hypothesis("exp-1")
        assert h.target_signal == "none"
        assert h.expected_effect == 0.0
        assert "autocorrelation" in h.confounders

    def test_signal_hypothesis_creation(self):
        h = create_signal_hypothesis("exp-1", "momentum", 0.5)
        assert h.target_signal == "momentum"
        assert h.expected_effect > 0

    def test_is_confirmed_by(self):
        h = create_signal_hypothesis("exp-1", "momentum", 0.5)
        assert h.is_confirmed_by("momentum")
        assert not h.is_confirmed_by("autocorrelation")

    def test_is_falsified_by(self):
        h = create_null_hypothesis("exp-1")
        assert h.is_falsified_by("autocorrelation")
        assert h.is_falsified_by("momentum")
        assert h.is_falsified_by("mean_reversion")
        assert not h.is_falsified_by("unknown_mechanism")

    def test_to_dict(self):
        h = create_null_hypothesis("exp-1")
        d = h.to_dict()
        assert "hypothesis_id" in d
        assert "claim" in d
        assert "confounders" in d


# ---------------------------------------------------------------------------
# Adversarial Epistemic Tests
#
# These verify that the system does NOT allow performance or DGP knowledge
# to substitute for actual observed mechanism evidence.
# ---------------------------------------------------------------------------


class TestAdversarialEpistemic:
    """The four impossibility invariants."""

    def test_high_sharpe_does_not_imply_predictable_mechanism(self):
        """A high Sharpe from the agent does NOT imply a mechanism was identified.

        If the agent gets a high Sharpe but we have no evidence about what
        mechanism produced it, the epistemic status must be INCONCLUSIVE.
        """
        world = generate_null_world("test", autocorrelation=0.0, seed=42)
        hypothesis = create_null_hypothesis("test")
        result = MechanismAttributionResult(
            world_id="test",
            world=world,
            hypothesis=hypothesis,
        )
        result.random = run_random_strategy(world)
        result.buyhold = run_buy_and_hold(world)
        result.momentum = run_momentum_strategy(world)
        result.oracle = run_oracle_strategy(world)
        # Simulate a profitable agent with NO mechanism identification
        result.agent = StrategyResult(
            strategy_name="Agent",
            world_id="test",
            sharpe_ratio=8.88,  # Unrealistically high — the original bug
            total_return=0.5,
            max_drawdown=-0.1,
            note="Unidentified mechanism",
        )
        _attribute_mechanism(result)
        # The system must NOT confirm the hypothesis just because Sharpe is high
        assert not result.hypothesis_confirmed
        # And must NOT refute it either
        assert not result.hypothesis_falsified
        # Must produce an epistemic evaluation
        assert result.epistemic_evaluation is not None
        assert result.epistemic_evaluation.status == EpistemicStatus.INCONCLUSIVE

    def test_predictable_mechanism_does_not_imply_identified_mechanism(self):
        """The DGP may contain a predictable structure (autocorrelation) that
        the agent did NOT identify. The epistemic evaluation must reflect
        what the agent actually found, not what was theoretically available.
        """
        world = generate_null_world("test", autocorrelation=0.5, seed=42)
        hypothesis = create_null_hypothesis("test")
        result = MechanismAttributionResult(
            world_id="test",
            world=world,
            hypothesis=hypothesis,
        )
        result.random = run_random_strategy(world)
        result.buyhold = run_buy_and_hold(world)
        result.momentum = run_momentum_strategy(world)
        result.oracle = run_oracle_strategy(world)
        # Agent found a strategy but it's just noise-fitting
        result.agent = StrategyResult(
            strategy_name="Agent",
            world_id="test",
            sharpe_ratio=0.3,  # Below threshold
            total_return=0.05,
            max_drawdown=-0.15,
            note="Noise fit",
        )
        _attribute_mechanism(result)
        # Even though momentum exploits AR, the agent didn't identify it
        # The hypothesis must not be refuted just because the DGP had structure
        assert not result.hypothesis_falsified

    def test_identified_mechanism_does_not_imply_hypothesis_support(self):
        """The agent may identify a mechanism that does NOT match the
        declared hypothesis. The hypothesis must not be confirmed.
        """
        world, _ = generate_known_signal_world(
            "test", signal_strength=0.5, autocorrelation=0.0, n_observations=252, seed=42
        )
        # Signal hypothesis: agent should find the known_sine signal
        hypothesis = create_signal_hypothesis("test", "known_sine", 0.5)
        result = MechanismAttributionResult(
            world_id="test",
            world=world,
            hypothesis=hypothesis,
        )
        result.random = run_random_strategy(world)
        result.buyhold = run_buy_and_hold(world)
        result.momentum = run_momentum_strategy(world)
        result.oracle = run_oracle_strategy(world)
        # Agent found momentum instead of signal
        result.agent = StrategyResult(
            strategy_name="Agent",
            world_id="test",
            sharpe_ratio=1.5,
            total_return=0.3,
            max_drawdown=-0.1,
            note="Found momentum, not signal",
        )
        _attribute_mechanism(result)
        # Agent did not find the declared signal — hypothesis not confirmed
        assert not result.hypothesis_confirmed

    def test_hypothesis_support_does_not_imply_governance_approval(self):
        """Even if the hypothesis is supported, governance may reject
        for other reasons (e.g., Sharpe below threshold, risk limits).
        """
        world, _ = generate_known_signal_world(
            "test", signal_strength=0.5, autocorrelation=0.0, n_observations=252, seed=42
        )
        hypothesis = create_signal_hypothesis("test", "known_sine", 0.5)
        result = MechanismAttributionResult(
            world_id="test",
            world=world,
            hypothesis=hypothesis,
        )
        result.random = run_random_strategy(world)
        result.buyhold = run_buy_and_hold(world)
        result.momentum = run_momentum_strategy(world)
        result.oracle = run_oracle_strategy(world)
        # Agent found signal but Sharpe is below governance threshold
        result.agent = StrategyResult(
            strategy_name="Agent",
            world_id="test",
            sharpe_ratio=0.3,  # Below 0.5 threshold
            total_return=0.05,
            max_drawdown=-0.1,
            note="Signal found but weak",
        )
        _attribute_mechanism(result)
        # Even if epistemic status is SUPPORTED, governance may reject
        if result.epistemic_evaluation and result.epistemic_evaluation.status == EpistemicStatus.SUPPORTED:
            assert not result.accepted  # Sharpe below threshold → not accepted


class TestNoAgentResult:
    """Without an agent result, the system must NOT confirm or falsify hypotheses."""

    def test_null_iid_no_agent_is_inconclusive(self):
        """Null IID world with no agent → INCONCLUSIVE, not confirmed."""
        world = generate_null_world("test", autocorrelation=0.0, seed=42)
        hypothesis = create_null_hypothesis("test")
        result = MechanismAttributionResult(
            world_id="test",
            world=world,
            hypothesis=hypothesis,
        )
        result.random = run_random_strategy(world)
        result.buyhold = run_buy_and_hold(world)
        result.momentum = run_momentum_strategy(world)
        result.oracle = run_oracle_strategy(world)
        # No agent result
        _attribute_mechanism(result)
        # No agent → no epistemic judgment possible
        assert not result.hypothesis_confirmed
        assert not result.hypothesis_falsified
        assert result.epistemic_evaluation is not None
        assert result.epistemic_evaluation.status == EpistemicStatus.INCONCLUSIVE

    def test_null_ar_no_agent_is_inconclusive(self):
        """Null AR world with no agent → INCONCLUSIVE, not falsified.

        Even though momentum exploits the AR, without an agent we cannot
        attribute mechanism. The null hypothesis must NOT be refuted.
        """
        world = generate_null_world("test", autocorrelation=0.5, seed=42)
        hypothesis = create_null_hypothesis("test")
        result = MechanismAttributionResult(
            world_id="test",
            world=world,
            hypothesis=hypothesis,
        )
        result.random = run_random_strategy(world)
        result.buyhold = run_buy_and_hold(world)
        result.momentum = run_momentum_strategy(world)
        result.oracle = run_oracle_strategy(world)
        # No agent result
        _attribute_mechanism(result)
        # No agent → no epistemic judgment
        assert not result.hypothesis_confirmed
        assert not result.hypothesis_falsified
        assert result.epistemic_evaluation is not None
        assert result.epistemic_evaluation.status == EpistemicStatus.INCONCLUSIVE

    def test_signal_iid_no_agent_is_inconclusive(self):
        """Signal world with no agent → INCONCLUSIVE, not confirmed.

        Without an agent, we don't know if the signal was recoverable.
        """
        world, _ = generate_known_signal_world(
            "test", signal_strength=0.5, autocorrelation=0.0, n_observations=252, seed=42
        )
        hypothesis = create_signal_hypothesis("test", "known_sine", 0.5)
        result = MechanismAttributionResult(
            world_id="test",
            world=world,
            hypothesis=hypothesis,
        )
        result.random = run_random_strategy(world)
        result.buyhold = run_buy_and_hold(world)
        result.momentum = run_momentum_strategy(world)
        result.oracle = run_oracle_strategy(world)
        # No agent result
        _attribute_mechanism(result)
        assert not result.hypothesis_confirmed
        assert not result.hypothesis_falsified
        assert result.epistemic_evaluation is not None
        assert result.epistemic_evaluation.status == EpistemicStatus.INCONCLUSIVE


class TestEpistemicEvaluation:
    """Direct tests of the epistemic evaluation function."""

    def test_insufficient_evidence_is_inconclusive(self):
        """A mechanism with too few observations is INCONCLUSIVE."""
        hypothesis = create_signal_hypothesis("test", "momentum", 0.5)
        mechanism = ObservedMechanismArtifact(
            mechanism_id="m1",
            experiment_id="e1",
            mechanism_type="momentum",
            n_observations=5,  # Too few
            n_trades=2,        # Too few
            sharpe_ratio=2.0,  # High Sharpe but meaningless
        )
        evaluation = evaluate_hypothesis(hypothesis, mechanism)
        assert evaluation.status == EpistemicStatus.INCONCLUSIVE
        assert "Insufficient evidence" in evaluation.reasoning

    def test_signal_not_observed_is_not_refuted(self):
        """Failing to recover a signal is NOT evidence the signal doesn't exist."""
        hypothesis = create_signal_hypothesis("test", "known_sine", 0.5)
        # Agent found a competing mechanism (momentum), not the declared signal
        mechanism = ObservedMechanismArtifact(
            mechanism_id="m1",
            experiment_id="e1",
            mechanism_type="momentum",  # Not the declared signal
            n_observations=252,
            n_trades=50,
            sharpe_ratio=1.5,
        )
        evaluation = evaluate_hypothesis(hypothesis, mechanism)
        # Agent found momentum, not the signal — this does NOT refute the
        # hypothesis that a signal exists. The signal might exist but the
        # agent chose a competing mechanism.
        assert evaluation.status == EpistemicStatus.INCONCLUSIVE

    def test_confounder_on_null_is_refuted(self):
        """Agent finds a confounder on a null hypothesis → REFUTED."""
        hypothesis = create_null_hypothesis("test")
        mechanism = ObservedMechanismArtifact(
            mechanism_id="m1",
            experiment_id="e1",
            mechanism_type="autocorrelation",  # Confounder
            n_observations=252,
            n_trades=50,
            sharpe_ratio=1.5,
            dependency_measure=0.3,  # Statistical evidence for this mechanism
        )
        evaluation = evaluate_hypothesis(hypothesis, mechanism)
        assert evaluation.status == EpistemicStatus.REFUTED

    def test_no_predictability_on_null_is_supported(self):
        """Agent finds no predictability on a null hypothesis → SUPPORTED."""
        hypothesis = create_null_hypothesis("test")
        mechanism = ObservedMechanismArtifact(
            mechanism_id="m1",
            experiment_id="e1",
            mechanism_type="none",
            n_observations=252,
            n_trades=5,  # Need >= 5 trades for statistical significance
            sharpe_ratio=0.05,
            dependency_measure=0.01,  # Very low — no real dependency
        )
        evaluation = evaluate_hypothesis(hypothesis, mechanism)
        assert evaluation.status == EpistemicStatus.SUPPORTED

    def test_signal_match_is_supported(self):
        """Agent finds the declared signal → SUPPORTED."""
        hypothesis = create_signal_hypothesis("test", "known_sine", 0.5)
        mechanism = ObservedMechanismArtifact(
            mechanism_id="m1",
            experiment_id="e1",
            mechanism_type="known_sine",  # Matches hypothesis
            n_observations=252,
            n_trades=50,
            sharpe_ratio=3.0,
            dependency_measure=0.5,  # Strong statistical evidence
        )
        evaluation = evaluate_hypothesis(hypothesis, mechanism)
        assert evaluation.status == EpistemicStatus.SUPPORTED

    def test_profitable_without_mechanism_is_not_supported(self):
        """High Sharpe without an ObservedMechanismArtifact → INCONCLUSIVE.

        This is the key adversarial invariant: profitability alone does
        NOT establish mechanism or hypothesis support.
        """
        hypothesis = create_signal_hypothesis("test", "momentum", 0.5)
        # Agent has high Sharpe but mechanism type is unknown
        mechanism = ObservedMechanismArtifact(
            mechanism_id="m1",
            experiment_id="e1",
            mechanism_type="unknown",
            n_observations=252,
            n_trades=50,
            sharpe_ratio=8.88,  # Very high
        )
        evaluation = evaluate_hypothesis(hypothesis, mechanism)
        # Unknown mechanism type → INCONCLUSIVE, not SUPPORTED
        assert evaluation.status == EpistemicStatus.INCONCLUSIVE
        # Even with Sharpe of 8.88


class TestGovernanceAcceptance:
    """Tests that governance acceptance is properly decoupled from epistemic status."""

    def test_inconclusive_hypothesis_not_accepted(self):
        """INCONCLUSIVE epistemic status → not accepted."""
        world = generate_null_world("test", autocorrelation=0.0, seed=42)
        hypothesis = create_null_hypothesis("test")
        result = MechanismAttributionResult(
            world_id="test",
            world=world,
            hypothesis=hypothesis,
        )
        result.random = run_random_strategy(world)
        result.buyhold = run_buy_and_hold(world)
        result.momentum = run_momentum_strategy(world)
        result.oracle = run_oracle_strategy(world)
        result.agent = StrategyResult(
            strategy_name="Agent",
            world_id="test",
            sharpe_ratio=1.5,
            total_return=0.3,
            max_drawdown=-0.1,
            note="Some profit",
        )
        _attribute_mechanism(result)
        # With no agent-mechanism match, must not accept
        if result.epistemic_evaluation:
            if result.epistemic_evaluation.status != EpistemicStatus.SUPPORTED:
                assert not result.accepted


# ---------------------------------------------------------------------------
# Matrix Integration Tests
# ---------------------------------------------------------------------------


class TestMatrixIntegration:
    def test_matrix_runs_without_agent(self):
        results = run_mechanism_attribution_matrix(
            signal_strengths=[0.0, 0.5],
            autocorrelations=[0.0, 0.3],
            seed=42,
            n_observations=252,
            run_agent=False,
        )
        assert len(results) == 4

    def test_matrix_has_all_strategies(self):
        results = run_mechanism_attribution_matrix(
            signal_strengths=[0.0],
            autocorrelations=[0.0],
            seed=42,
            n_observations=252,
            run_agent=False,
        )
        r = results["null-iid-s42"]
        assert r.random is not None
        assert r.buyhold is not None
        assert r.momentum is not None
        assert r.oracle is not None

    def test_matrix_without_agent_all_inconclusive(self):
        """Without agent results, all epistemic evaluations must be INCONCLUSIVE."""
        results = run_mechanism_attribution_matrix(
            signal_strengths=[0.0, 0.5, 1.0],
            autocorrelations=[0.0, 0.5],
            seed=42,
            n_observations=252,
            run_agent=False,
        )
        for world_id, r in results.items():
            assert r.epistemic_evaluation is not None, f"{world_id} has no epistemic evaluation"
            assert r.epistemic_evaluation.status == EpistemicStatus.INCONCLUSIVE, \
                f"{world_id}: expected INCONCLUSIVE, got {r.epistemic_evaluation.status}"
            assert not r.hypothesis_confirmed, f"{world_id}: hypothesis confirmed without agent"
            assert not r.hypothesis_falsified, f"{world_id}: hypothesis falsified without agent"


# ---------------------------------------------------------------------------
# Strategy Tests (unchanged)
# ---------------------------------------------------------------------------


class TestStrategies:
    def test_random_strategy(self):
        world = generate_null_world("test", seed=42)
        result = run_random_strategy(world)
        assert isinstance(result, StrategyResult)
        assert result.strategy_name == "Random"

    def test_buy_and_hold(self):
        world = generate_null_world("test", seed=42)
        result = run_buy_and_hold(world)
        assert isinstance(result, StrategyResult)
        assert result.strategy_name == "BuyHold"

    def test_momentum_strategy(self):
        world = generate_null_world("test", autocorrelation=0.5, seed=42)
        result = run_momentum_strategy(world)
        assert isinstance(result, StrategyResult)
        assert result.strategy_name == "Momentum"

    def test_oracle_no_signal(self):
        world = generate_null_world("test", seed=42)
        result = run_oracle_strategy(world)
        assert result.sharpe_ratio == 0.0

    def test_oracle_with_signal(self):
        world, _ = generate_known_signal_world(
            "test", signal_strength=0.5, n_observations=252, seed=42
        )
        result = run_oracle_strategy(world)
        assert result.sharpe_ratio > 0.5
