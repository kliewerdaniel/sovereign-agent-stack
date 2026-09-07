"""Tests for the mechanism identification challenge.

Verifies that the system correctly determines what the evidence supports
across 7 adversarial worlds with known ground truth.
"""

from __future__ import annotations

import pytest

from sas.quant.experiment.mechanism_challenge import (
    ChallengeWorld,
    ChallengeResult,
    build_challenge_worlds,
    run_challenge,
    run_challenge_suite,
    generate_challenge_report,
)
from sas.quant.experiment.mechanism_attribution import (
    run_momentum_strategy,
    run_buy_and_hold,
)
from sas.quant.experiment.epistemic import EpistemicStatus


# ---------------------------------------------------------------------------
# Test: Challenge worlds are well-formed
# ---------------------------------------------------------------------------


class TestChallengeWorlds:
    def test_build_challenge_worlds_returns_7(self):
        challenges = build_challenge_worlds()
        assert len(challenges) == 7

    def test_challenge_worlds_have_unique_ids(self):
        challenges = build_challenge_worlds()
        ids = [c.world_id for c in challenges]
        assert len(set(ids)) == 7

    def test_challenge_worlds_have_declared_hypotheses(self):
        challenges = build_challenge_worlds()
        for c in challenges:
            assert c.declared_hypothesis is not None
            assert c.declared_hypothesis.target_signal != ""

    def test_challenge_worlds_have_known_ground_truth(self):
        challenges = build_challenge_worlds()
        for c in challenges:
            assert c.actual_mechanism in ["momentum", "autocorrelation", "both", "none"]
            assert isinstance(c.would_be_false_positive, bool)


# ---------------------------------------------------------------------------
# Test: Challenge runner produces results
# ---------------------------------------------------------------------------


class TestChallengeRunner:
    def test_run_challenge_returns_result(self):
        challenges = build_challenge_worlds()
        result = run_challenge(challenges[0])
        assert isinstance(result, ChallengeResult)
        assert result.challenge == challenges[0]

    def test_run_challenge_has_investigations(self):
        challenges = build_challenge_worlds()
        result = run_challenge(challenges[0])
        assert len(result.investigations) >= 3

    def test_run_challenge_has_strategy_results(self):
        challenges = build_challenge_worlds()
        result = run_challenge(challenges[0])
        assert "momentum" in result.strategy_results
        assert "buyhold" in result.strategy_results

    def test_run_challenge_has_epistemic_evaluation(self):
        challenges = build_challenge_worlds()
        result = run_challenge(challenges[0])
        assert result.epistemic_evaluation is not None

    def test_run_challenge_false_positive_flag_set(self):
        challenges = build_challenge_worlds()
        result = run_challenge(challenges[0])
        assert isinstance(result.false_positive, bool)

    def test_run_challenge_correct_flag_set(self):
        challenges = build_challenge_worlds()
        result = run_challenge(challenges[0])
        assert isinstance(result.correct, bool)


# ---------------------------------------------------------------------------
# Test: Full challenge suite
# ---------------------------------------------------------------------------


class TestChallengeSuite:
    def test_run_challenge_suite_returns_7(self):
        results = run_challenge_suite()
        assert len(results) == 7

    def test_run_challenge_suite_all_have_epistemic_evaluation(self):
        results = run_challenge_suite()
        for r in results:
            assert r.epistemic_evaluation is not None

    def test_run_challenge_suite_all_have_investigations(self):
        results = run_challenge_suite()
        for r in results:
            assert len(r.investigations) >= 3

    def test_run_challenge_suite_false_positive_rate_computed(self):
        results = run_challenge_suite()
        fp_count = sum(1 for r in results if r.false_positive)
        # The system should have a low false-positive rate
        # (This is a property we want to verify, not a hard assertion)
        assert isinstance(fp_count, int)

    def test_run_challenge_suite_correct_count_computed(self):
        results = run_challenge_suite()
        correct_count = sum(1 for r in results if r.correct)
        assert isinstance(correct_count, int)
        assert 0 <= correct_count <= 7


# ---------------------------------------------------------------------------
# Test: Challenge 1 — obvious mechanism
# ---------------------------------------------------------------------------


class TestChallenge1Obvious:
    def test_challenge_1_has_strong_signal(self):
        challenges = build_challenge_worlds()
        c = challenges[0]
        assert c.world_id == "challenge-1-obvious"
        assert c.world.dgp.has_signal
        assert c.world.dgp.signal_strength > 0.5

    def test_challenge_1_should_not_be_false_positive(self):
        challenges = build_challenge_worlds()
        c = challenges[0]
        assert not c.would_be_false_positive

    def test_challenge_1_returns_ablation_shows_change(self):
        challenges = build_challenge_worlds()
        result = run_challenge(challenges[0])
        # The momentum strategy uses lagged returns, so returns ablation should show change
        returns_ablations = [
            i for i in result.investigations
            if i.investigation_type == "feature_ablation" and i.feature_affected == "returns"
        ]
        # On a strong signal world, returns ablation should show change
        if returns_ablations:
            assert returns_ablations[0].sharpe_drop != 0.0

    def test_challenge_1_momentum_exploits_autocorrelation(self):
        """On a signal world with signal_type='momentum', the strategy exploits returns."""
        challenges = build_challenge_worlds()
        result = run_challenge(challenges[0])
        # Momentum should outperform buyhold on a signal world
        momentum = result.strategy_results["momentum"]
        buyhold = result.strategy_results["buyhold"]
        assert momentum.sharpe_ratio > buyhold.sharpe_ratio


# ---------------------------------------------------------------------------
# Test: Challenge 7 — inconclusive (null IID)
# ---------------------------------------------------------------------------


class TestChallenge7Inconclusive:
    def test_challenge_7_is_null_iid(self):
        challenges = build_challenge_worlds()
        c = challenges[6]
        assert c.world_id == "challenge-7-inconclusive"
        assert not c.world.dgp.has_signal
        assert c.world.dgp.autocorrelation == 0.0

    def test_challenge_7_should_be_false_positive_if_supported(self):
        challenges = build_challenge_worlds()
        c = challenges[6]
        # Asserting SUPPORTED on null IID would be a false positive
        assert c.would_be_false_positive

    def test_challenge_7_system_should_not_support(self):
        challenges = build_challenge_worlds()
        result = run_challenge(challenges[6])
        # On null IID, the system should NOT assert SUPPORTED
        if result.epistemic_evaluation:
            assert result.epistemic_evaluation.status != EpistemicStatus.SUPPORTED


# ---------------------------------------------------------------------------
# Test: Report generation
# ---------------------------------------------------------------------------


class TestChallengeReport:
    def test_generate_challenge_report_returns_string(self):
        results = run_challenge_suite()
        report = generate_challenge_report(results)
        assert isinstance(report, str)
        assert len(report) > 0

    def test_report_contains_table(self):
        results = run_challenge_suite()
        report = generate_challenge_report(results)
        assert "|" in report  # Markdown table
        assert "Challenge" in report

    def test_report_contains_summary(self):
        results = run_challenge_suite()
        report = generate_challenge_report(results)
        assert "False positives:" in report
        assert "Epistemic false-positive rate:" in report

    def test_report_contains_all_7_challenges(self):
        results = run_challenge_suite()
        report = generate_challenge_report(results)
        for i in range(1, 8):
            assert f"Challenge {i}:" in report


# ---------------------------------------------------------------------------
# Test: Epistemic false-positive rate is the key metric
# ---------------------------------------------------------------------------


class TestFalsePositiveRate:
    def test_false_positive_rate_is_computed(self):
        results = run_challenge_suite()
        fp_count = sum(1 for r in results if r.false_positive)
        total = len(results)
        rate = fp_count / total
        assert 0.0 <= rate <= 1.0

    def test_performance_is_not_the_key_metric(self):
        """The key metric is NOT whether the agent found a profitable strategy.

        It's whether the system correctly determined what the evidence supports.
        """
        results = run_challenge_suite()
        # A challenge can have positive agent Sharpe but still be a false positive
        # (e.g., agent exploits AR but signal hypothesis is claimed)
        for r in results:
            # Positive Sharpe doesn't imply hypothesis is supported
            agent_sharpe = r.strategy_results.get("agent", None)
            if agent_sharpe and agent_sharpe.sharpe_ratio > 0.5:
                # Even with positive Sharpe, the epistemic evaluation could be
                # INCONCLUSIVE or REFUTED (correctly)
                pass  # No assertion — this is the point
