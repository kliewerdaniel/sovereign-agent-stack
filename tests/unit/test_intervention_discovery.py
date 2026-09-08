"""Tests for Intervention Discovery & Authority Experiment."""

from __future__ import annotations

import pytest

from sas.quant.experiment.intervention_discovery import (
    AgentHypothesis,
    HypothesisType,
    InterventionDiscoveryResult,
    DiscoveryExperimentResult,
    generate_candidate_hypotheses,
    select_intervention_target,
    run_intervention_discovery_test,
    run_intervention_discovery_experiment,
    generate_discovery_experiment_report,
)
from sas.quant.experiment.synthetic_worlds import generate_signal_world
from sas.quant.experiment.mechanism_attribution import run_momentum_strategy
from sas.quant.experiment.typed_propositions import (
    PropositionType,
    InterventionType,
    can_inform,
    TypedProposition,
    EvidenceBundle,
    evaluate_typed_proposition,
    run_all_impossibility_proofs,
    generate_authority_matrix_report,
)


# ---------------------------------------------------------------------------
# Test: Hypothesis Generation
# ---------------------------------------------------------------------------


class TestHypothesisGeneration:
    def test_signal_world_generates_hypotheses(self):
        world = generate_signal_world(
            world_id="test_signal",
            signal_strength=0.5,
            autocorrelation=0.0,
            seed=42,
        )
        result = run_momentum_strategy(world, lookback=5)
        hypotheses = generate_candidate_hypotheses(world, result.sharpe_ratio)
        assert len(hypotheses) > 0

    def test_ar_world_generates_hypotheses(self):
        world = generate_signal_world(
            world_id="test_ar",
            signal_strength=0.0,
            autocorrelation=0.5,
            seed=42,
        )
        result = run_momentum_strategy(world, lookback=5)
        hypotheses = generate_candidate_hypotheses(world, result.sharpe_ratio)
        assert len(hypotheses) > 0

    def test_high_sharpe_generates_spurious_hypothesis(self):
        world = generate_signal_world(
            world_id="test_high_sharpe",
            signal_strength=0.5,
            autocorrelation=0.3,
            seed=42,
        )
        hypotheses = generate_candidate_hypotheses(world, 3.0)
        hypothesis_types = [h.hypothesis_type for h in hypotheses]
        assert HypothesisType.SPURIOUS_CORRELATION in hypothesis_types


# ---------------------------------------------------------------------------
# Test: Intervention Selection
# ---------------------------------------------------------------------------


class TestInterventionSelection:
    def test_select_intervention_returns_mechanism(self):
        world = generate_signal_world(
            world_id="test_selection",
            signal_strength=0.5,
            autocorrelation=0.0,
            seed=42,
        )
        result = run_momentum_strategy(world, lookback=5)
        hypotheses = generate_candidate_hypotheses(world, result.sharpe_ratio)
        intervention = select_intervention_target(hypotheses, world)
        assert intervention.target in ["signal_component", "autocorrelation"]

    def test_select_intervention_with_no_hypotheses_defaults(self):
        world = generate_signal_world(
            world_id="test_default",
            signal_strength=0.0,
            autocorrelation=0.0,
            seed=42,
        )
        intervention = select_intervention_target([], world)
        assert intervention.target == "autocorrelation"


# ---------------------------------------------------------------------------
# Test: Intervention Discovery Test
# ---------------------------------------------------------------------------


class TestInterventionDiscovery:
    def test_discovery_test_runs(self):
        world = generate_signal_world(
            world_id="test_discovery",
            signal_strength=0.5,
            autocorrelation=0.0,
            seed=42,
        )
        result = run_intervention_discovery_test(
            world,
            lambda w: run_momentum_strategy(w, lookback=5),
            "signal_component",
        )
        assert isinstance(result, InterventionDiscoveryResult)
        assert result.sharpe_before != 0.0

    def test_discovery_test_measures_sharpe_drop(self):
        world = generate_signal_world(
            world_id="test_drop",
            signal_strength=0.0,
            autocorrelation=0.5,
            seed=42,
        )
        result = run_intervention_discovery_test(
            world,
            lambda w: run_momentum_strategy(w, lookback=5),
            "autocorrelation",
        )
        # AR world with momentum strategy should show significant drop
        assert result.sharpe_drop > 0.0


# ---------------------------------------------------------------------------
# Test: Typed Propositions
# ---------------------------------------------------------------------------


class TestTypedPropositions:
    def test_feature_cannot_inform_mechanism(self):
        assert not can_inform(
            InterventionType.FEATURE_ABLATION,
            PropositionType.MECHANISM_DEPENDENCY,
        )

    def test_mechanism_can_inform_mechanism(self):
        assert can_inform(
            InterventionType.MECHANISM_REMOVAL,
            PropositionType.MECHANISM_DEPENDENCY,
        )

    def test_holdout_can_inform_generalization(self):
        assert can_inform(
            InterventionType.HOLDOUT,
            PropositionType.GENERALIZATION,
        )

    def test_holdout_cannot_inform_causality(self):
        assert not can_inform(
            InterventionType.HOLDOUT,
            PropositionType.CAUSAL_CLAIM,
        )


# ---------------------------------------------------------------------------
# Test: Authority Violations
# ---------------------------------------------------------------------------


class TestAuthorityViolations:
    def test_feature_evidence_rejected_for_mechanism_proposition(self):
        proposition = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal component drives returns",
        )
        evidence = EvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.FEATURE_ABLATION,
            target="signal",
            effect_size=0.8,
            description="Signal ablation reduced Sharpe",
        )
        result = evaluate_typed_proposition(proposition, [evidence])
        assert result.status == "INCONCLUSIVE"
        assert len(result.authority_violations) > 0

    def test_mechanism_evidence_accepted_for_mechanism_proposition(self):
        proposition = TypedProposition(
            proposition_id="p2",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal component drives returns",
        )
        evidence = EvidenceBundle(
            evidence_id="e2",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.8,
            description="Signal component removal reduced Sharpe",
        )
        result = evaluate_typed_proposition(proposition, [evidence])
        assert result.authorized_evidence_count > 0


# ---------------------------------------------------------------------------
# Test: Impossibility Proofs
# ---------------------------------------------------------------------------


class TestImpossibilityProofs:
    def test_observational_equivalence_bound(self):
        proofs = run_all_impossibility_proofs()
        assert len(proofs) > 0
        for proof in proofs:
            assert proof.result is True

    def test_sharpe_cannot_authorize_mechanism(self):
        proofs = run_all_impossibility_proofs()
        sharpe_proof = [p for p in proofs if "Sharpe" in p.claim]
        assert len(sharpe_proof) > 0
        assert sharpe_proof[0].result is True

    def test_feature_cannot_authorize_mechanism(self):
        proofs = run_all_impossibility_proofs()
        feature_proof = [p for p in proofs if "feature" in p.claim.lower()]
        assert len(feature_proof) > 0
        assert feature_proof[0].result is True


# ---------------------------------------------------------------------------
# Test: Report Generation
# ---------------------------------------------------------------------------


class TestReportGeneration:
    def test_authority_matrix_report(self):
        report = generate_authority_matrix_report()
        assert "Authority Matrix" in report
        assert "Feature interventions cannot authorize mechanism claims" in report

    def test_discovery_experiment_report(self):
        result = run_intervention_discovery_experiment(
            signal_strengths=[0.5],
            ar_coeffs=[0.3],
            seeds=[42],
        )
        report = generate_discovery_experiment_report(result)
        assert "Intervention Discovery" in report
        assert "Correct target rate" in report


# ---------------------------------------------------------------------------
# Test: Full Experiment
# ---------------------------------------------------------------------------


class TestFullExperiment:
    def test_small_experiment_runs(self):
        result = run_intervention_discovery_experiment(
            signal_strengths=[0.5, 1.0],
            ar_coeffs=[0.3],
            seeds=[42],
        )
        assert result.total > 0
        assert 0.0 <= result.correct_target_rate <= 1.0

    def test_experiment_produces_results(self):
        result = run_intervention_discovery_experiment(
            signal_strengths=[0.5],
            ar_coeffs=[0.3, 0.5],
            seeds=[42, 123],
        )
        assert len(result.results) > 0
