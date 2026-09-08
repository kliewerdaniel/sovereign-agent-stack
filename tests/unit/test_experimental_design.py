"""Tests for Experimental Design Authority & Discriminative Power."""

from __future__ import annotations

import pytest

from sas.quant.experiment.experimental_design import (
    DesignAuthorityResult,
    DesignAuthorityExperiment,
    DesignSufficiencyResult,
    ExperimentalDesignArtifact,
    FailureType,
    FailureClassification,
    analyze_confounders,
    identify_competing_mechanisms,
    compute_discriminative_power,
    evaluate_design_sufficiency,
    run_design_authority_experiment,
    generate_design_authority_report,
)
from sas.quant.experiment.synthetic_worlds import generate_signal_world
from sas.quant.experiment.intervention_semantics import MechanismIntervention
from sas.quant.experiment.intervention_discovery import (
    AgentHypothesis,
    HypothesisType,
    generate_candidate_hypotheses,
)
from sas.quant.experiment.mechanism_attribution import run_momentum_strategy


# ---------------------------------------------------------------------------
# Test: Confound Analysis
# ---------------------------------------------------------------------------


class TestConfoundAnalysis:
    def test_signal_world_with_ar_confound(self):
        world = generate_signal_world(
            world_id="test_confound",
            signal_strength=0.5,
            autocorrelation=0.3,
            seed=42,
        )
        result = run_momentum_strategy(world, lookback=5)
        hypotheses = generate_candidate_hypotheses(world, result.sharpe_ratio)
        best = max(hypotheses, key=lambda h: h.confidence)

        intervention = MechanismIntervention("signal_component", "remove")
        confounders = analyze_confounders(world, best, intervention)
        assert "autocorrelation" in confounders

    def test_ar_world_with_signal_confound(self):
        world = generate_signal_world(
            world_id="test_ar_signal",
            signal_strength=0.5,
            autocorrelation=0.3,
            seed=42,
        )
        result = run_momentum_strategy(world, lookback=5)
        hypotheses = generate_candidate_hypotheses(world, result.sharpe_ratio)
        best = max(hypotheses, key=lambda h: h.confidence)

        intervention = MechanismIntervention("autocorrelation", "remove")
        confounders = analyze_confounders(world, best, intervention)
        assert "latent_signal" in confounders

    def test_pure_signal_no_confound(self):
        world = generate_signal_world(
            world_id="test_pure_signal",
            signal_strength=0.5,
            autocorrelation=0.0,
            seed=42,
        )
        result = run_momentum_strategy(world, lookback=5)
        hypotheses = generate_candidate_hypotheses(world, result.sharpe_ratio)
        best = max(hypotheses, key=lambda h: h.confidence)

        intervention = MechanismIntervention("signal_component", "remove")
        confounders = analyze_confounders(world, best, intervention)
        assert len(confounders) == 0


# ---------------------------------------------------------------------------
# Test: Competing Mechanisms
# ---------------------------------------------------------------------------


class TestCompetingMechanisms:
    def test_signal_competitions(self):
        world = generate_signal_world(
            world_id="test_competitions",
            signal_strength=0.5,
            autocorrelation=0.3,
            seed=42,
        )
        hypothesis = AgentHypothesis(
            hypothesis_id="h1",
            hypothesis_type=HypothesisType.LAGGED_RETURN_STRUCTURE,
            description="Test",
            confidence=0.7,
        )
        competing = identify_competing_mechanisms(world, hypothesis)
        assert "latent_signal" in competing

    def test_spurious_competitions(self):
        world = generate_signal_world(
            world_id="test_spurious",
            signal_strength=0.5,
            autocorrelation=0.3,
            seed=42,
        )
        hypothesis = AgentHypothesis(
            hypothesis_id="h2",
            hypothesis_type=HypothesisType.SPURIOUS_CORRELATION,
            description="Test",
            confidence=0.5,
        )
        competing = identify_competing_mechanisms(world, hypothesis)
        assert len(competing) > 0


# ---------------------------------------------------------------------------
# Test: Discriminative Power
# ---------------------------------------------------------------------------


class TestDiscriminativePower:
    def test_perfect_discrimination(self):
        world = generate_signal_world(
            world_id="test_perfect",
            signal_strength=0.5,
            autocorrelation=0.0,
            seed=42,
        )
        hypothesis = AgentHypothesis(
            hypothesis_id="h1",
            hypothesis_type=HypothesisType.EXOGENOUS_PREDICTIVE_COMPONENT,
            description="Test",
            confidence=0.8,
        )
        intervention = MechanismIntervention("signal_component", "remove")
        power = compute_discriminative_power(world, hypothesis, intervention, [])
        assert power >= 0.5

    def test_low_discrimination(self):
        world = generate_signal_world(
            world_id="test_low",
            signal_strength=0.5,
            autocorrelation=0.5,
            seed=42,
        )
        hypothesis = AgentHypothesis(
            hypothesis_id="h1",
            hypothesis_type=HypothesisType.LAGGED_RETURN_STRUCTURE,
            description="Test",
            confidence=0.6,
        )
        intervention = MechanismIntervention("signal_component", "remove")
        power = compute_discriminative_power(world, hypothesis, intervention, ["latent_signal"])
        assert power < 0.5


# ---------------------------------------------------------------------------
# Test: Design Sufficiency
# ---------------------------------------------------------------------------


class TestDesignSufficiency:
    def test_sufficient_design(self):
        world = generate_signal_world(
            world_id="test_sufficient",
            signal_strength=0.5,
            autocorrelation=0.0,
            seed=42,
        )
        hypothesis = AgentHypothesis(
            hypothesis_id="h1",
            hypothesis_type=HypothesisType.EXOGENOUS_PREDICTIVE_COMPONENT,
            description="Test",
            confidence=0.8,
        )
        intervention = MechanismIntervention("signal_component", "remove")
        result = evaluate_design_sufficiency(world, hypothesis, intervention)
        assert isinstance(result, DesignSufficiencyResult)
        assert result.is_sufficient

    def test_insufficient_design(self):
        world = generate_signal_world(
            world_id="test_insufficient",
            signal_strength=0.5,
            autocorrelation=0.5,
            seed=42,
        )
        hypothesis = AgentHypothesis(
            hypothesis_id="h1",
            hypothesis_type=HypothesisType.LAGGED_RETURN_STRUCTURE,
            description="Test",
            confidence=0.6,
        )
        intervention = MechanismIntervention("signal_component", "remove")
        result = evaluate_design_sufficiency(world, hypothesis, intervention)
        assert not result.is_sufficient


# ---------------------------------------------------------------------------
# Test: Full Experiment
# ---------------------------------------------------------------------------


class TestDesignAuthorityExperiment:
    def test_small_experiment_runs(self):
        result = run_design_authority_experiment(
            signal_strengths=[0.5],
            ar_coeffs=[0.3],
            seeds=[42],
        )
        assert result.total > 0
        assert 0.0 <= result.sufficient_design_rate <= 1.0

    def test_experiment_produces_results(self):
        result = run_design_authority_experiment(
            signal_strengths=[0.5, 1.0],
            ar_coeffs=[0.3],
            seeds=[42, 123],
        )
        assert len(result.results) > 0
        assert result.failure_taxonomy is not None


# ---------------------------------------------------------------------------
# Test: Report Generation
# ---------------------------------------------------------------------------


class TestReportGeneration:
    def test_design_authority_report(self):
        result = run_design_authority_experiment(
            signal_strengths=[0.5],
            ar_coeffs=[0.3],
            seeds=[42],
        )
        report = generate_design_authority_report(result)
        assert "Experimental Design Authority" in report
        assert "Sufficient design rate" in report
        assert "Failure Taxonomy" in report


# ---------------------------------------------------------------------------
# Test: Failure Taxonomy
# ---------------------------------------------------------------------------


class TestFailureTaxonomy:
    def test_failure_types(self):
        assert FailureType.HYPOTHESIS_GENERATION == "hypothesis_generation"
        assert FailureType.EXPERIMENTAL_DESIGN == "experimental_design"
        assert FailureType.EVIDENCE_SUFFICIENCY == "evidence_sufficiency"
        assert FailureType.SEMANTIC_MAPPING == "semantic_mapping"
        assert FailureType.EVALUATOR == "evaluator"
        assert FailureType.GOVERNANCE == "governance"

    def test_failure_classification(self):
        fc = FailureClassification(
            failure_type=FailureType.EXPERIMENTAL_DESIGN,
            description="Test failure",
            expected="discriminative experiment",
            actual="non-discriminative experiment",
        )
        assert fc.failure_type == FailureType.EXPERIMENTAL_DESIGN
