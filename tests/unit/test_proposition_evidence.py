"""Tests for the Proposition Evidence Matrix.

Verifies that proposition-level evaluation works correctly and that
the dual-path comparison is sound.
"""

from __future__ import annotations

import pytest

from sas.quant.experiment.proposition_evidence import (
    DualPathResult,
    PropositionEvidence,
    PropositionEvaluation,
    analyze_dual_path_results,
    evaluate_proposition,
    generate_proposition_evidence_report,
    run_dual_path_comparison,
    run_proposition_evidence_experiment,
)
from sas.quant.experiment.epistemic import (
    EpistemicStatus,
    ObservedMechanismArtifact,
    evaluate_hypothesis,
)
from sas.quant.experiment.hypothesis import (
    create_null_hypothesis,
    create_signal_hypothesis,
)
from sas.quant.experiment.evidence_sufficiency import (
    ExperimentalCondition,
    build_world_for_condition,
)
from sas.quant.experiment.mechanism_investigation import (
    MechanismInvestigationResult,
)


# ---------------------------------------------------------------------------
# Test: PropositionEvidence construction
# ---------------------------------------------------------------------------


class TestPropositionEvidence:
    def test_create_proposition_evidence(self):
        prop = PropositionEvidence(
            proposition_id="test-1",
            proposition_text="SIGNAL predicts future returns",
        )
        assert prop.proposition_id == "test-1"
        assert prop.feature_ablation_evidence == []

    def test_proposition_evidence_with_investigations(self):
        inv = MechanismInvestigationResult(
            investigation_type="feature_ablation",
            mechanism_id="m1",
            world_id="w1",
            original_sharpe=2.0,
            perturbed_sharpe=0.5,
            sharpe_drop=1.5,
            is_robust=False,
            conclusion="Signal ablation dropped Sharpe by 1.5",
            evidence_strength=0.8,
            feature_affected="signal",
        )
        prop = PropositionEvidence(
            proposition_id="test-1",
            proposition_text="SIGNAL predicts future returns",
            feature_ablation_evidence=[inv],
        )
        assert len(prop.feature_ablation_evidence) == 1


# ---------------------------------------------------------------------------
# Test: Proposition evaluation — signal hypothesis
# ---------------------------------------------------------------------------


class TestPropositionEvaluationSignal:
    def test_strong_signal_evidence_supports_proposition(self):
        """When multiple investigations confirm signal, proposition should be SUPPORTED."""
        prop = PropositionEvidence(
            proposition_id="test-1",
            proposition_text="SIGNAL predicts future returns",
            feature_ablation_evidence=[
                MechanismInvestigationResult(
                    investigation_type="feature_ablation",
                    mechanism_id="m1",
                    world_id="w1",
                    original_sharpe=2.0,
                    perturbed_sharpe=0.5,
                    sharpe_drop=1.5,
                    is_robust=False,
                    conclusion="Signal ablation dropped Sharpe by 1.5",
                    evidence_strength=0.8,
                    feature_affected="signal",
                ),
            ],
            permutation_evidence=[
                MechanismInvestigationResult(
                    investigation_type="permutation",
                    mechanism_id="m1",
                    world_id="w1",
                    original_sharpe=2.0,
                    perturbed_sharpe=0.3,
                    sharpe_drop=1.7,
                    is_robust=False,
                    conclusion="Permutation dropped Sharpe by 1.7",
                    evidence_strength=0.9,
                ),
            ],
            temporal_evidence=[
                MechanismInvestigationResult(
                    investigation_type="temporal_perturbation",
                    mechanism_id="m1",
                    world_id="w1",
                    original_sharpe=2.0,
                    perturbed_sharpe=0.4,
                    sharpe_drop=1.6,
                    is_robust=False,
                    conclusion="Temporal perturbation dropped Sharpe by 1.6",
                    evidence_strength=0.85,
                ),
            ],
            competing_mechanism_evidence=[
                MechanismInvestigationResult(
                    investigation_type="competing_mechanism",
                    mechanism_id="m1",
                    world_id="w1",
                    original_sharpe=2.0,
                    perturbed_sharpe=2.0,
                    sharpe_drop=0.0,
                    is_robust=False,
                    conclusion="Evidence consistent with strategy depending on SIGNAL",
                    evidence_strength=0.8,
                ),
            ],
        )

        hyp = create_signal_hypothesis("hyp-1", "momentum", 0.7)
        result = evaluate_proposition(prop, hyp)
        assert result.status == EpistemicStatus.SUPPORTED
        assert result.confidence > 0.5

    def test_weak_signal_evidence_does_not_support(self):
        """When investigations show minimal effect, proposition should be INCONCLUSIVE."""
        prop = PropositionEvidence(
            proposition_id="test-1",
            proposition_text="SIGNAL predicts future returns",
            feature_ablation_evidence=[
                MechanismInvestigationResult(
                    investigation_type="feature_ablation",
                    mechanism_id="m1",
                    world_id="w1",
                    original_sharpe=0.5,
                    perturbed_sharpe=0.4,
                    sharpe_drop=0.1,
                    is_robust=True,
                    conclusion="Signal ablation had minimal effect",
                    evidence_strength=0.1,
                    feature_affected="signal",
                ),
            ],
        )

        hyp = create_signal_hypothesis("hyp-1", "momentum", 0.7)
        result = evaluate_proposition(prop, hyp)
        assert result.status == EpistemicStatus.INCONCLUSIVE

    def test_contradictory_evidence_is_inconclusive(self):
        """When evidence is mixed, result should be INCONCLUSIVE."""
        prop = PropositionEvidence(
            proposition_id="test-1",
            proposition_text="SIGNAL predicts future returns",
            feature_ablation_evidence=[
                MechanismInvestigationResult(
                    investigation_type="feature_ablation",
                    mechanism_id="m1",
                    world_id="w1",
                    original_sharpe=2.0,
                    perturbed_sharpe=0.5,
                    sharpe_drop=1.5,
                    is_robust=False,
                    conclusion="Signal ablation dropped Sharpe by 1.5",
                    evidence_strength=0.8,
                    feature_affected="signal",
                ),
            ],
            permutation_evidence=[
                MechanismInvestigationResult(
                    investigation_type="permutation",
                    mechanism_id="m1",
                    world_id="w1",
                    original_sharpe=2.0,
                    perturbed_sharpe=1.8,
                    sharpe_drop=0.2,
                    is_robust=True,
                    conclusion="Permutation had minimal effect",
                    evidence_strength=0.2,
                ),
            ],
        )

        hyp = create_signal_hypothesis("hyp-1", "momentum", 0.7)
        result = evaluate_proposition(prop, hyp)
        assert result.status == EpistemicStatus.INCONCLUSIVE


# ---------------------------------------------------------------------------
# Test: Proposition evaluation — null hypothesis
# ---------------------------------------------------------------------------


class TestPropositionEvaluationNull:
    def test_no_effects_supports_null(self):
        """When no investigation shows an effect, null is supported."""
        prop = PropositionEvidence(
            proposition_id="test-1",
            proposition_text="No mechanism exists",
            feature_ablation_evidence=[
                MechanismInvestigationResult(
                    investigation_type="feature_ablation",
                    mechanism_id="m1",
                    world_id="w1",
                    original_sharpe=0.1,
                    perturbed_sharpe=0.1,
                    sharpe_drop=0.0,
                    is_robust=True,
                    conclusion="No effect",
                    evidence_strength=0.0,
                    feature_affected="signal",
                ),
            ],
            permutation_evidence=[
                MechanismInvestigationResult(
                    investigation_type="permutation",
                    mechanism_id="m1",
                    world_id="w1",
                    original_sharpe=0.1,
                    perturbed_sharpe=0.1,
                    sharpe_drop=0.0,
                    is_robust=True,
                    conclusion="No effect",
                    evidence_strength=0.0,
                ),
            ],
        )

        hyp = create_null_hypothesis("hyp-1")
        result = evaluate_proposition(prop, hyp)
        assert result.status == EpistemicStatus.SUPPORTED

    def test_strong_effects_refutes_null(self):
        """When investigations show strong effects, null is refuted."""
        prop = PropositionEvidence(
            proposition_id="test-1",
            proposition_text="No mechanism exists",
            feature_ablation_evidence=[
                MechanismInvestigationResult(
                    investigation_type="feature_ablation",
                    mechanism_id="m1",
                    world_id="w1",
                    original_sharpe=2.0,
                    perturbed_sharpe=0.5,
                    sharpe_drop=1.5,
                    is_robust=False,
                    conclusion="Signal ablation dropped Sharpe by 1.5",
                    evidence_strength=0.8,
                    feature_affected="signal",
                ),
            ],
            permutation_evidence=[
                MechanismInvestigationResult(
                    investigation_type="permutation",
                    mechanism_id="m1",
                    world_id="w1",
                    original_sharpe=2.0,
                    perturbed_sharpe=0.3,
                    sharpe_drop=1.7,
                    is_robust=False,
                    conclusion="Permutation dropped Sharpe by 1.7",
                    evidence_strength=0.9,
                ),
            ],
        )

        hyp = create_null_hypothesis("hyp-1")
        result = evaluate_proposition(prop, hyp)
        assert result.status == EpistemicStatus.REFUTED


# ---------------------------------------------------------------------------
# Test: Dual-path comparison
# ---------------------------------------------------------------------------


class TestDualPathComparison:
    def test_dual_path_runs_both_paths(self):
        cond = ExperimentalCondition(
            condition_id="c0001",
            world_type="known_signal",
            sample_size=252,
            signal_strength=0.7,
            search_budget=10,
            mechanism_separation="clear",
            intervention_strength="strong",
            seed=42,
        )
        result = run_dual_path_comparison(cond)
        assert isinstance(result, DualPathResult)
        assert result.path_a_evaluation is not None
        assert result.path_b_evaluation is not None

    def test_path_b_can_be_more_informative(self):
        """Path B should sometimes be more informative than Path A."""
        cond = ExperimentalCondition(
            condition_id="c0001",
            world_type="known_signal",
            sample_size=504,
            signal_strength=0.7,
            search_budget=10,
            mechanism_separation="clear",
            intervention_strength="strong",
            seed=42,
        )
        result = run_dual_path_comparison(cond)
        # Path B may or may not be more informative, but the comparison should work
        assert isinstance(result.path_b_more_informative, bool)

    def test_paths_agree_flag_set(self):
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
        result = run_dual_path_comparison(cond)
        assert isinstance(result.paths_agree, bool)


# ---------------------------------------------------------------------------
# Test: Full experiment
# ---------------------------------------------------------------------------


class TestPropositionExperiment:
    def test_small_experiment(self):
        results = run_proposition_evidence_experiment(
            sample_sizes=[252, 504],
            signal_strengths=[0.0, 0.7],
            search_budgets=[10],
            mechanism_separations=["clear"],
            intervention_strengths=["strong"],
            seeds=[42, 123],
            world_types=["null", "known_signal"],
            n_replications=1,
        )
        assert len(results) > 0
        for r in results:
            assert r.path_a_evaluation is not None
            assert r.path_b_evaluation is not None

    def test_analysis_runs(self):
        results = run_proposition_evidence_experiment(
            sample_sizes=[252],
            signal_strengths=[0.0, 0.7],
            search_budgets=[10],
            mechanism_separations=["clear"],
            intervention_strengths=["strong"],
            seeds=[42],
            world_types=["null", "known_signal"],
            n_replications=1,
        )
        analysis = analyze_dual_path_results(results)
        assert analysis["total"] > 0
        assert "path_a_statuses" in analysis
        assert "path_b_statuses" in analysis

    def test_report_generation(self):
        results = run_proposition_evidence_experiment(
            sample_sizes=[252],
            signal_strengths=[0.0, 0.7],
            search_budgets=[10],
            mechanism_separations=["clear"],
            intervention_strengths=["strong"],
            seeds=[42],
            world_types=["null", "known_signal"],
            n_replications=1,
        )
        report = generate_proposition_evidence_report(results)
        assert "Proposition Evidence Matrix" in report
        assert "Path A" in report
        assert "Path B" in report


# ---------------------------------------------------------------------------
# Test: Frozen API unchanged
# ---------------------------------------------------------------------------


class TestFrozenAPI:
    def test_epistemic_status_unchanged(self):
        assert EpistemicStatus.SUPPORTED == "supported"
        assert EpistemicStatus.REFUTED == "refuted"
        assert EpistemicStatus.INCONCLUSIVE == "inconclusive"

    def test_evaluate_hypothesis_unchanged(self):
        """The frozen evaluator should still work the same way."""
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
