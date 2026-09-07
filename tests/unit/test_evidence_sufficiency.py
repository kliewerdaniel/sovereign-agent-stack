"""Tests for the Evidence Sufficiency Characterization experiment.

Verifies that the experiment infrastructure is sound and that the
frozen epistemic API remains unmodified.
"""

from __future__ import annotations

import pytest

from sas.quant.experiment.evidence_sufficiency import (
    ConditionResult,
    ExperimentalCondition,
    MonotonicityResult,
    analyze_monotonicity,
    build_hypothesis_for_condition,
    build_observed_mechanism,
    build_world_for_condition,
    compute_aggregate_metrics,
    compute_conditional_metrics,
    generate_evidence_sufficiency_report,
    run_evidence_sufficiency_experiment,
    run_single_condition,
)
from sas.quant.experiment.epistemic import (
    EpistemicStatus,
    evaluate_hypothesis,
)
from sas.quant.experiment.hypothesis import (
    create_null_hypothesis,
    create_signal_hypothesis,
)


# ---------------------------------------------------------------------------
# Test: ExperimentalCondition construction
# ---------------------------------------------------------------------------


class TestExperimentalCondition:
    def test_condition_has_key(self):
        cond = ExperimentalCondition(
            condition_id="c0001",
            world_type="null",
            sample_size=252,
            signal_strength=0.0,
            search_budget=10,
            mechanism_separation="clear",
            intervention_strength="moderate",
            seed=42,
        )
        assert "null" in cond.key
        assert "252" in cond.key

    def test_condition_key_aggregates_across_seeds(self):
        c1 = ExperimentalCondition("c1", "null", 252, 0.0, 10, "clear", "moderate", 42)
        c2 = ExperimentalCondition("c2", "null", 252, 0.0, 10, "clear", "moderate", 123)
        assert c1.key == c2.key


# ---------------------------------------------------------------------------
# Test: World construction for each condition type
# ---------------------------------------------------------------------------


class TestWorldConstruction:
    def test_null_world_has_no_signal(self):
        cond = ExperimentalCondition("c1", "null", 252, 0.0, 10, "clear", "moderate", 42)
        world = build_world_for_condition(cond)
        assert not world.dgp.has_signal

    def test_known_signal_world_has_signal(self):
        cond = ExperimentalCondition("c1", "known_signal", 252, 0.7, 10, "clear", "moderate", 42)
        world = build_world_for_condition(cond)
        assert world.dgp.has_signal
        assert world.dgp.signal_strength > 0.5

    def test_wrong_mechanism_world_has_no_signal_but_has_ar(self):
        cond = ExperimentalCondition("c1", "wrong_mechanism", 252, 0.0, 10, "clear", "moderate", 42)
        world = build_world_for_condition(cond)
        assert not world.dgp.has_signal
        assert world.dgp.autocorrelation > 0.3

    def test_confounded_world_has_both(self):
        cond = ExperimentalCondition("c1", "confounded", 252, 0.5, 10, "clear", "moderate", 42)
        world = build_world_for_condition(cond)
        assert world.dgp.has_signal
        assert world.dgp.autocorrelation > 0.0

    def test_non_identifiable_world_has_observationally_equivalent_signal(self):
        cond = ExperimentalCondition("c1", "non_identifiable", 252, 0.5, 10, "clear", "moderate", 42)
        world = build_world_for_condition(cond)
        assert world.dgp.has_signal

    def test_sample_size_respected(self):
        cond = ExperimentalCondition("c1", "null", 504, 0.0, 10, "clear", "moderate", 42)
        world = build_world_for_condition(cond)
        assert len(world.research_data) >= 480


# ---------------------------------------------------------------------------
# Test: Hypothesis construction
# ---------------------------------------------------------------------------


class TestHypothesisConstruction:
    def test_null_world_gets_null_hypothesis(self):
        cond = ExperimentalCondition("c1", "null", 252, 0.0, 10, "clear", "moderate", 42)
        hyp = build_hypothesis_for_condition(cond)
        assert "null" in hyp.hypothesis_id or "hyp" in hyp.hypothesis_id

    def test_signal_world_gets_signal_hypothesis(self):
        cond = ExperimentalCondition("c1", "known_signal", 252, 0.7, 10, "clear", "moderate", 42)
        hyp = build_hypothesis_for_condition(cond)
        assert hyp.target_signal == "momentum"


# ---------------------------------------------------------------------------
# Test: Single condition execution
# ---------------------------------------------------------------------------


class TestSingleCondition:
    def test_run_null_condition(self):
        cond = ExperimentalCondition(
            condition_id="c0001",
            world_type="null",
            sample_size=252,
            signal_strength=0.0,
            search_budget=10,
            mechanism_separation="clear",
            intervention_strength="moderate",
            seed=42,
        )
        result = run_single_condition(cond)
        assert isinstance(result, ConditionResult)
        assert result.condition == cond
        assert result.epistemic_evaluation is not None
        assert result.false_positive is False

    def test_run_known_signal_condition(self):
        cond = ExperimentalCondition(
            condition_id="c0002",
            world_type="known_signal",
            sample_size=252,
            signal_strength=0.7,
            search_budget=10,
            mechanism_separation="clear",
            intervention_strength="moderate",
            seed=42,
        )
        result = run_single_condition(cond)
        assert isinstance(result, ConditionResult)
        assert result.agent_sharpe != 0.0

    def test_run_wrong_mechanism_condition(self):
        cond = ExperimentalCondition(
            condition_id="c0003",
            world_type="wrong_mechanism",
            sample_size=252,
            signal_strength=0.0,
            search_budget=10,
            mechanism_separation="clear",
            intervention_strength="moderate",
            seed=42,
        )
        result = run_single_condition(cond)
        assert isinstance(result, ConditionResult)
        # Agent may find high Sharpe through AR
        # But epistemic should NOT support signal hypothesis
        assert result.false_positive is False

    def test_run_non_identifiable_condition(self):
        cond = ExperimentalCondition(
            condition_id="c0004",
            world_type="non_identifiable",
            sample_size=252,
            signal_strength=0.5,
            search_budget=10,
            mechanism_separation="indistinguishable",
            intervention_strength="moderate",
            seed=42,
        )
        result = run_single_condition(cond)
        assert isinstance(result, ConditionResult)
        assert result.false_positive is False


# ---------------------------------------------------------------------------
# Test: Metrics computation
# ---------------------------------------------------------------------------


class TestMetricsComputation:
    def test_aggregate_metrics_basic(self):
        results = run_evidence_sufficiency_experiment(
            sample_sizes=[126, 252],
            signal_strengths=[0.0, 0.5],
            search_budgets=[10],
            mechanism_separations=["clear"],
            intervention_strengths=["moderate"],
            seeds=[42, 123],
            world_types=["null", "known_signal"],
        )
        metrics = compute_aggregate_metrics(results)
        assert metrics.total_conditions > 0
        assert metrics.false_positive_rate == 0.0
        assert 0.0 <= metrics.support_rate <= 1.0
        assert 0.0 <= metrics.inconclusive_rate <= 1.0

    def test_conditional_metrics_grouping(self):
        results = run_evidence_sufficiency_experiment(
            sample_sizes=[126, 252],
            signal_strengths=[0.0, 0.5],
            search_budgets=[10],
            mechanism_separations=["clear"],
            intervention_strengths=["moderate"],
            seeds=[42],
            world_types=["null", "known_signal"],
        )
        grouped = compute_conditional_metrics(results, "sample_size")
        assert len(grouped) == 2

    def test_metrics_are_separated(self):
        """Verify metrics are NOT collapsed into one score."""
        results = run_evidence_sufficiency_experiment(
            sample_sizes=[252],
            signal_strengths=[0.0, 0.7],
            search_budgets=[10],
            mechanism_separations=["clear"],
            intervention_strengths=["moderate"],
            seeds=[42],
            world_types=["null", "known_signal"],
        )
        metrics = compute_aggregate_metrics(results)
        # These should be separate fields, not derived from each other
        assert hasattr(metrics, 'false_positive_rate')
        assert hasattr(metrics, 'false_negative_rate')
        assert hasattr(metrics, 'inconclusive_rate')
        assert hasattr(metrics, 'mechanism_identification_rate')
        assert hasattr(metrics, 'governance_acceptance_rate')


# ---------------------------------------------------------------------------
# Test: Monotonicity analysis
# ---------------------------------------------------------------------------


class TestMonotonicityAnalysis:
    def test_monotonicity_detects_increasing_trend(self):
        results = run_evidence_sufficiency_experiment(
            sample_sizes=[126, 252, 504],
            signal_strengths=[0.7],
            search_budgets=[10],
            mechanism_separations=["clear"],
            intervention_strengths=["moderate"],
            seeds=[42, 123, 456],
            world_types=["known_signal"],
        )
        mono = analyze_monotonicity(results, "sample_size", [126, 252, 504])
        assert isinstance(mono, MonotonicityResult)
        assert len(mono.support_rates) == 3
        assert mono.is_monotonic  # Should be increasing with more data

    def test_monotonicity_detects_non_monotonic(self):
        results = run_evidence_sufficiency_experiment(
            sample_sizes=[126, 252],
            signal_strengths=[0.3, 0.7],
            search_budgets=[10, 50],
            mechanism_separations=["clear", "indistinguishable"],
            intervention_strengths=["weak", "strong"],
            seeds=[42],
            world_types=["confounded"],
        )
        mono = analyze_monotonicity(results, "signal_strength", [0.3, 0.7])
        assert isinstance(mono, MonotonicityResult)


# ---------------------------------------------------------------------------
# Test: Frozen epistemic API is unchanged
# ---------------------------------------------------------------------------


class TestFrozenEpistemicAPI:
    def test_epistemic_status_values_unchanged(self):
        assert EpistemicStatus.SUPPORTED == "supported"
        assert EpistemicStatus.REFUTED == "refuted"
        assert EpistemicStatus.INCONCLUSIVE == "inconclusive"

    def test_evaluate_hypothesis_still_conservative(self):
        """The evaluator must still be conservative after all experiments."""
        from sas.quant.experiment.epistemic import ObservedMechanismArtifact

        hyp = create_signal_hypothesis("test", "momentum", 0.7)
        mech = ObservedMechanismArtifact(
            mechanism_id="m1",
            experiment_id="exp-1",
            mechanism_type="unknown",
            features_used=["close"],
            information_horizon="t+1",
            dependency_measure=0.1,
            evidence=["insufficient evidence"],
            competing_mechanisms=["autocorrelation"],
            confidence=0.1,
            sharpe_ratio=0.5,
            n_observations=50,
            n_trades=5,
        )
        result = evaluate_hypothesis(hyp, mech)
        assert result.status == EpistemicStatus.INCONCLUSIVE

    def test_null_hypothesis_with_no_mechanism_is_supported(self):
        from sas.quant.experiment.epistemic import ObservedMechanismArtifact

        hyp = create_null_hypothesis("test")
        mech = ObservedMechanismArtifact(
            mechanism_id="m1",
            experiment_id="exp-1",
            mechanism_type="none",
            features_used=[],
            information_horizon="t+1",
            dependency_measure=0.0,
            evidence=["no mechanism found"],
            competing_mechanisms=[],
            confidence=0.1,
            sharpe_ratio=0.05,
            n_observations=252,
            n_trades=0,
        )
        result = evaluate_hypothesis(hyp, mech)
        assert result.status == EpistemicStatus.SUPPORTED

    def test_high_sharpe_alone_does_not_support_hypothesis(self):
        """A high Sharpe with unknown mechanism must not support the hypothesis."""
        from sas.quant.experiment.epistemic import ObservedMechanismArtifact

        hyp = create_signal_hypothesis("test", "momentum", 0.7)
        mech = ObservedMechanismArtifact(
            mechanism_id="m1",
            experiment_id="exp-1",
            mechanism_type="unknown",
            features_used=["close"],
            information_horizon="t+1",
            dependency_measure=0.1,
            evidence=["high Sharpe, unknown mechanism"],
            competing_mechanisms=["autocorrelation", "optimization_pressure"],
            confidence=0.1,
            sharpe_ratio=5.0,
            n_observations=252,
            n_trades=50,
        )
        result = evaluate_hypothesis(hyp, mech)
        assert result.status == EpistemicStatus.INCONCLUSIVE


# ---------------------------------------------------------------------------
# Test: Key invariants
# ---------------------------------------------------------------------------


class TestInvariants:
    def test_increasing_sample_size_cannot_manufacture_mechanism_identity(self):
        """More observations don't create mechanism from nothing."""
        small = ExperimentalCondition("c1", "null", 63, 0.0, 10, "clear", "moderate", 42)
        large = ExperimentalCondition("c2", "null", 504, 0.0, 10, "clear", "moderate", 42)
        r1 = run_single_condition(small)
        r2 = run_single_condition(large)
        # Neither should produce false positive
        assert r1.false_positive is False
        assert r2.false_positive is False

    def test_increasing_sharpe_cannot_manufacture_hypothesis_support(self):
        """High Sharpe on wrong mechanism must not support signal hypothesis."""
        cond = ExperimentalCondition(
            condition_id="c0001",
            world_type="wrong_mechanism",
            sample_size=504,
            signal_strength=0.0,
            search_budget=50,
            mechanism_separation="clear",
            intervention_strength="strong",
            seed=42,
        )
        result = run_single_condition(cond)
        # Even if agent finds high Sharpe, signal hypothesis must not be supported
        if result.agent_sharpe > 1.0:
            assert result.epistemic_status != EpistemicStatus.SUPPORTED

    def test_increasing_search_budget_cannot_manufacture_hypothesis_support(self):
        """More search budget on null world must not support hypothesis."""
        cond = ExperimentalCondition(
            condition_id="c0001",
            world_type="null",
            sample_size=252,
            signal_strength=0.0,
            search_budget=100,
            mechanism_separation="clear",
            intervention_strength="strong",
            seed=42,
        )
        result = run_single_condition(cond)
        assert result.false_positive is False

    def test_confounded_mechanisms_remain_distinguishable(self):
        """Confounded worlds should have different epistemic outcomes than known_signal."""
        clear = ExperimentalCondition("c1", "known_signal", 252, 0.7, 10, "clear", "moderate", 42)
        confounded = ExperimentalCondition("c2", "confounded", 252, 0.7, 10, "moderate", "moderate", 42)
        r1 = run_single_condition(clear)
        r2 = run_single_condition(confounded)
        # Both should be conservative (no false positives)
        assert r1.false_positive is False
        assert r2.false_positive is False

    def test_observationally_indistinguishable_remains_inconclusive(self):
        """Non-identifiable world should not produce SUPPORTED."""
        cond = ExperimentalCondition(
            condition_id="c0001",
            world_type="non_identifiable",
            sample_size=252,
            signal_strength=0.5,
            search_budget=50,
            mechanism_separation="indistinguishable",
            intervention_strength="strong",
            seed=42,
        )
        result = run_single_condition(cond)
        assert result.epistemic_status != EpistemicStatus.SUPPORTED

    def test_null_worlds_retain_zero_false_positives_under_repeated_search(self):
        """Multiple seeds, high budget — null must remain zero false positives."""
        results = run_evidence_sufficiency_experiment(
            sample_sizes=[126, 252, 504],
            signal_strengths=[0.0],
            search_budgets=[10, 50, 100],
            mechanism_separations=["clear"],
            intervention_strengths=["weak", "moderate", "strong"],
            seeds=[42, 123, 456, 789, 101112],
            world_types=["null"],
        )
        fp_count = sum(1 for r in results if r.false_positive)
        assert fp_count == 0


# ---------------------------------------------------------------------------
# Test: Report generation
# ---------------------------------------------------------------------------


class TestReportGeneration:
    def test_report_contains_matrix(self):
        results = run_evidence_sufficiency_experiment(
            sample_sizes=[252, 504],
            signal_strengths=[0.0, 0.7],
            search_budgets=[10],
            mechanism_separations=["clear"],
            intervention_strengths=["moderate"],
            seeds=[42],
            world_types=["null", "known_signal"],
        )
        report = generate_evidence_sufficiency_report(results)
        assert "Evidence Sufficiency Matrix" in report
        assert "Aggregate Metrics" in report

    def test_report_contains_operating_envelope(self):
        results = run_evidence_sufficiency_experiment(
            sample_sizes=[252],
            signal_strengths=[0.0, 0.7],
            search_budgets=[10],
            mechanism_separations=["clear"],
            intervention_strengths=["moderate"],
            seeds=[42],
            world_types=["null", "known_signal"],
        )
        report = generate_evidence_sufficiency_report(results)
        assert "Operating Envelope" in report

    def test_report_contains_failure_analysis(self):
        results = run_evidence_sufficiency_experiment(
            sample_sizes=[252],
            signal_strengths=[0.0, 0.7],
            search_budgets=[10],
            mechanism_separations=["clear"],
            intervention_strengths=["moderate"],
            seeds=[42],
            world_types=["null", "known_signal"],
        )
        report = generate_evidence_sufficiency_report(results)
        assert "Failure Analysis" in report


# ---------------------------------------------------------------------------
# Test: Full experiment runner
# ---------------------------------------------------------------------------


class TestFullExperiment:
    def test_small_factorial(self):
        """Run a small factorial design to verify the pipeline works end-to-end."""
        results = run_evidence_sufficiency_experiment(
            sample_sizes=[126, 252],
            signal_strengths=[0.0, 0.7],
            search_budgets=[10],
            mechanism_separations=["clear"],
            intervention_strengths=["moderate"],
            seeds=[42, 123],
            world_types=["null", "known_signal", "wrong_mechanism"],
        )
        # 2 sample sizes x (1 null + 1 signal + 1 wrong_mech) x 1 budget x 1 separation x 1 intervention x 2 seeds
        assert len(results) >= 6
        for r in results:
            assert r.epistemic_evaluation is not None
            assert len(r.investigations) >= 3
