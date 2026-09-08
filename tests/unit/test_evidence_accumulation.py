"""Tests for Evidence Accumulation Experiment."""

from __future__ import annotations

import pytest

from sas.quant.experiment.evidence_accumulation import (
    ExperimentType,
    ExperimentResult,
    run_experiment,
    run_evidence_accumulation_experiment,
    generate_experiment_report,
    _create_single_strong,
    _create_many_independent,
    _create_many_dependent,
    _create_many_contradictory,
    _create_many_convergent,
)
from sas.quant.experiment.evidence_structure import (
    EvidenceAccumulator,
    EvidenceProfile,
)
from sas.quant.experiment.typed_propositions import (
    InterventionType,
)


# ---------------------------------------------------------------------------
# Test: Experiment Constructors
# ---------------------------------------------------------------------------


class TestExperimentConstructors:
    def test_single_strong(self):
        bundles = _create_single_strong()
        assert len(bundles) == 1
        assert bundles[0].effect_size == 0.8

    def test_many_independent(self):
        bundles = _create_many_independent(10)
        assert len(bundles) == 10
        assert len(set(b.seed for b in bundles)) == 10

    def test_many_dependent(self):
        bundles = _create_many_dependent(10)
        assert len(bundles) == 10
        assert len(set(b.seed for b in bundles)) == 1

    def test_many_contradictory(self):
        bundles = _create_many_contradictory(10)
        assert len(bundles) == 10
        effects = [b.effect_size for b in bundles]
        assert any(e > 0 for e in effects)
        assert any(e < 0 for e in effects)

    def test_many_convergent(self):
        bundles = _create_many_convergent(10)
        assert len(bundles) == 10
        # All use FEATURE_ABLATION (wrong type for mechanism)
        assert all(
            b.intervention_type == InterventionType.FEATURE_ABLATION
            for b in bundles
        )


# ---------------------------------------------------------------------------
# Test: Single Experiments
# ---------------------------------------------------------------------------


class TestSingleExperiments:
    def test_single_strong_result(self):
        result = run_experiment(ExperimentType.SINGLE_STRONG)
        assert result.experiment_type == ExperimentType.SINGLE_STRONG
        assert result.n_evidence == 1

    def test_many_independent_result(self):
        result = run_experiment(ExperimentType.MANY_INDEPENDENT, n_evidence=10)
        assert result.experiment_type == ExperimentType.MANY_INDEPENDENT
        assert result.n_evidence == 10

    def test_many_dependent_result(self):
        result = run_experiment(ExperimentType.MANY_DEPENDENT, n_evidence=10)
        assert result.experiment_type == ExperimentType.MANY_DEPENDENT
        assert result.n_evidence == 10

    def test_many_contradictory_result(self):
        result = run_experiment(ExperimentType.MANY_CONTRADICTORY, n_evidence=10)
        assert result.experiment_type == ExperimentType.MANY_CONTRADICTORY
        assert result.n_evidence == 10

    def test_many_convergent_result(self):
        result = run_experiment(ExperimentType.MANY_CONVERGENT, n_evidence=10)
        assert result.experiment_type == ExperimentType.MANY_CONVERGENT
        assert result.n_evidence == 10


# ---------------------------------------------------------------------------
# Test: Experiment Suite
# ---------------------------------------------------------------------------


class TestExperimentSuite:
    def test_all_experiments_run(self):
        results = run_evidence_accumulation_experiment(n_evidence=5)
        assert len(results) == 5

    def test_experiment_types(self):
        results = run_evidence_accumulation_experiment(n_evidence=5)
        types = {r.experiment_type for r in results}
        assert types == {
            ExperimentType.SINGLE_STRONG,
            ExperimentType.MANY_INDEPENDENT,
            ExperimentType.MANY_DEPENDENT,
            ExperimentType.MANY_CONTRADICTORY,
            ExperimentType.MANY_CONVERGENT,
        }

    def test_report_generation(self):
        results = run_evidence_accumulation_experiment(n_evidence=5)
        report = generate_experiment_report(results)
        assert "Evidence Accumulation Experiment Report" in report
        assert "Scalar unique statuses" in report
        assert "Structured unique statuses" in report

    def test_report_has_detailed_results(self):
        results = run_evidence_accumulation_experiment(n_evidence=5)
        report = generate_experiment_report(results)
        for r in results:
            assert r.experiment_type.value in report


# ---------------------------------------------------------------------------
# Test: Invariant Verification
# ---------------------------------------------------------------------------


class TestInvariantVerification:
    def test_more_evidence_not_equal_stronger(self):
        """more evidence ≠ stronger evidence."""
        results = run_evidence_accumulation_experiment(n_evidence=10)
        single_strong = next(
            r for r in results
            if r.experiment_type == ExperimentType.SINGLE_STRONG
        )
        many_dependent = next(
            r for r in results
            if r.experiment_type == ExperimentType.MANY_DEPENDENT
        )

        # Both may be INCONCLUSIVE (different reasons), but the structured
        # profile should differ
        assert single_strong.profile.replication == 1
        assert many_dependent.profile.replication == 10

    def test_more_observations_not_more_independent(self):
        """more observations ≠ more independent evidence."""
        results = run_evidence_accumulation_experiment(n_evidence=10)
        many_independent = next(
            r for r in results
            if r.experiment_type == ExperimentType.MANY_INDEPENDENT
        )
        many_dependent = next(
            r for r in results
            if r.experiment_type == ExperimentType.MANY_DEPENDENT
        )

        # Independent should have higher independence score
        assert many_independent.profile.independence > many_dependent.profile.independence

    def test_many_dependent_not_supported(self):
        """Many dependent pieces should NOT be SUPPORTED."""
        result = run_experiment(ExperimentType.MANY_DEPENDENT, n_evidence=10)
        # Low independence should prevent SUPPORTED
        assert result.structured_status != "SUPPORTED"

    def test_many_independent_supported(self):
        """Many independent pieces SHOULD be SUPPORTED."""
        result = run_experiment(ExperimentType.MANY_INDEPENDENT, n_evidence=10)
        assert result.structured_status == "SUPPORTED"

    def test_contradictory_not_supported(self):
        """Contradictory evidence should NOT be SUPPORTED."""
        result = run_experiment(ExperimentType.MANY_CONTRADICTORY, n_evidence=10)
        assert result.structured_status != "SUPPORTED"

    def test_convergent_not_supported(self):
        """Convergent but non-discriminative evidence should NOT be SUPPORTED."""
        result = run_experiment(ExperimentType.MANY_CONVERGENT, n_evidence=10)
        assert result.structured_status != "SUPPORTED"

    def test_single_strong_inconclusive(self):
        """Single strong evidence should be INCONCLUSIVE (needs replication)."""
        result = run_experiment(ExperimentType.SINGLE_STRONG)
        assert result.structured_status == "INCONCLUSIVE"
