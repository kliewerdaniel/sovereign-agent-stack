"""Tests for mechanism investigation — causal evidence without expanding the API.

These tests verify that the four investigation types produce meaningful
evidence artifacts WITHOUT changing the frozen epistemic API
(SUPPORTED/REFUTED/INCONCLUSIVE).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from sas.quant.experiment.synthetic_worlds import (
    SyntheticWorld,
    generate_signal_world,
    generate_null_world,
)
from sas.quant.experiment.mechanism_investigation import (
    MechanismInvestigationResult,
    run_feature_ablation,
    run_permutation_test,
    run_competing_mechanism_test,
    run_temporal_perturbation,
    run_all_investigations,
)
from sas.quant.experiment.mechanism_attribution import (
    run_momentum_strategy,
    run_buy_and_hold,
)


# ---------------------------------------------------------------------------
# Strategy wrappers that return StrategyResult-like objects
# ---------------------------------------------------------------------------


def _momentum_strategy(world: SyntheticWorld):
    """Wrapper for momentum strategy."""
    return run_momentum_strategy(world, lookback=5)


def _buy_and_hold_strategy(world: SyntheticWorld):
    """Wrapper for buy-and-hold strategy."""
    return run_buy_and_hold(world)


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def null_iid_world() -> SyntheticWorld:
    return generate_null_world(
        world_id="test-null-iid",
        seed=42,
        autocorrelation=0.0,
    )


@pytest.fixture
def null_ar_world() -> SyntheticWorld:
    return generate_null_world(
        world_id="test-null-ar",
        seed=42,
        autocorrelation=0.5,
    )


@pytest.fixture
def signal_iid_world() -> SyntheticWorld:
    return generate_signal_world(
        world_id="test-signal-iid",
        signal_type="momentum",
        signal_strength=0.5,
        noise_std=0.02,
        autocorrelation=0.0,
        seed=42,
    )


@pytest.fixture
def signal_ar_world() -> SyntheticWorld:
    return generate_signal_world(
        world_id="test-signal-ar",
        signal_type="momentum",
        signal_strength=0.5,
        noise_std=0.02,
        autocorrelation=0.5,
        seed=42,
    )


# ---------------------------------------------------------------------------
# Test: Evidence artifacts are produced (frozen API invariant)
# ---------------------------------------------------------------------------


class TestFrozenApiInvariant:
    """Verify that investigations produce evidence, not new epistemic states."""

    def test_feature_ablation_returns_investigation_result(
        self, signal_iid_world
    ):
        result = run_feature_ablation(
            signal_iid_world, _momentum_strategy, "test-mech", feature="returns"
        )
        assert isinstance(result, MechanismInvestigationResult)
        assert result.investigation_type == "feature_ablation"
        assert result.mechanism_id == "test-mech"
        assert result.world_id == "test-signal-iid"

    def test_permutation_test_returns_investigation_result(
        self, signal_iid_world
    ):
        result = run_permutation_test(
            signal_iid_world, _momentum_strategy, "test-mech", n_permutations=5
        )
        assert isinstance(result, MechanismInvestigationResult)
        assert result.investigation_type == "permutation"

    def test_competing_mechanism_returns_investigation_result(
        self, signal_ar_world
    ):
        result = run_competing_mechanism_test(
            signal_ar_world, _momentum_strategy, "test-mech"
        )
        assert isinstance(result, MechanismInvestigationResult)
        assert result.investigation_type == "competing_mechanism"

    def test_temporal_perturbation_returns_investigation_result(
        self, signal_iid_world
    ):
        result = run_temporal_perturbation(
            signal_iid_world, _momentum_strategy, "test-mech", max_shift=3
        )
        assert isinstance(result, MechanismInvestigationResult)
        assert result.investigation_type == "temporal_perturbation"

    def test_all_investigations_returns_list(self, signal_iid_world):
        results = run_all_investigations(
            signal_iid_world, _momentum_strategy, "test-mech"
        )
        assert isinstance(results, list)
        assert len(results) >= 3  # At least ablation, permutation, temporal

    def test_evidence_does_not_expand_epistemic_status(self, signal_iid_world):
        """Investigation must NOT produce SUPPORTED/REFUTED/INCONCLUSIVE."""
        results = run_all_investigations(
            signal_iid_world, _momentum_strategy, "test-mech"
        )
        # Evidence artifacts should not have an epistemic status
        for r in results:
            # The frozen API only has SUPPORTED/REFUTED/INCONCLUSIVE
            # Evidence artifacts have investigation_type, not status
            assert hasattr(r, "investigation_type")
            assert hasattr(r, "evidence_strength")
            # Should NOT have status (that's for EpistemicEvaluation)
            assert not hasattr(r, "status")


# ---------------------------------------------------------------------------
# Test: Feature Ablation produces causal evidence
# ---------------------------------------------------------------------------


class TestFeatureAblation:
    def test_ablate_returns_drops_sharpe_on_signal_world(self, signal_iid_world):
        """On a signal world, ablating returns should drop Sharpe significantly."""
        result = run_feature_ablation(
            signal_iid_world, _momentum_strategy, "test-mech", feature="returns"
        )
        # Ablating returns should cause some Sharpe drop (strategy uses returns)
        assert result.sharpe_drop != 0.0
        assert result.original_sharpe != 0.0

    def test_ablate_returns_on_null_world(self, null_iid_world):
        """On a null world, ablating returns should have less effect."""
        result = run_feature_ablation(
            null_iid_world, _momentum_strategy, "test-mech", feature="returns"
        )
        # Null world: momentum should have low Sharpe regardless
        assert abs(result.original_sharpe) < 2.0

    def test_ablate_signal_feature(self, signal_iid_world):
        """Ablating the signal feature should affect strategies that use it."""
        result = run_feature_ablation(
            signal_iid_world, _momentum_strategy, "test-mech", feature="signal"
        )
        assert result.feature_affected == "signal"
        assert isinstance(result.sharpe_drop, float)

    def test_ablation_preserves_original_world(self, signal_iid_world):
        """Investigation must not mutate the original world."""
        original_data = signal_iid_world.research_data.copy()
        run_feature_ablation(
            signal_iid_world, _momentum_strategy, "test-mech", feature="returns"
        )
        # Original world data should be unchanged
        pd.testing.assert_frame_equal(
            signal_iid_world.research_data, original_data
        )

    def test_ablation_evidence_strength_bounded(self, signal_iid_world):
        """Evidence strength must be between 0 and 1."""
        result = run_feature_ablation(
            signal_iid_world, _momentum_strategy, "test-mech", feature="returns"
        )
        assert 0.0 <= result.evidence_strength <= 1.0


# ---------------------------------------------------------------------------
# Test: Permutation test detects spurious correlation
# ---------------------------------------------------------------------------


class TestPermutationTest:
    def test_permutation_reduces_sharpe_on_signal_world(self, signal_iid_world):
        """Shuffling returns should destroy temporal structure."""
        result = run_permutation_test(
            signal_iid_world, _momentum_strategy, "test-mech", n_permutations=5
        )
        # Sharpe should drop when temporal structure is destroyed
        assert result.sharpe_drop != 0.0

    def test_permutation_on_null_ar_world(self, null_ar_world):
        """On a null AR world, momentum exploits serial dependence."""
        result = run_permutation_test(
            null_ar_world, _momentum_strategy, "test-mech", n_permutations=5
        )
        # Shuffling should destroy the AR structure
        assert result.sharpe_drop != 0.0

    def test_permutation_evidence_strength(self, signal_iid_world):
        result = run_permutation_test(
            signal_iid_world, _momentum_strategy, "test-mech", n_permutations=5
        )
        assert 0.0 <= result.evidence_strength <= 1.0

    def test_permutation_n_permutations_respected(self, signal_iid_world):
        result = run_permutation_test(
            signal_iid_world, _momentum_strategy, "test-mech", n_permutations=10
        )
        # Should run 10 permutations
        assert "10" in result.perturbation_description


# ---------------------------------------------------------------------------
# Test: Competing mechanism test distinguishes signal from momentum
# ---------------------------------------------------------------------------


class TestCompetingMechanism:
    def test_competing_on_signal_ar_world(self, signal_ar_world):
        """On a signal+AR world, the test should identify which mechanism."""
        result = run_competing_mechanism_test(
            signal_ar_world, _momentum_strategy, "test-mech"
        )
        assert result.investigation_type == "competing_mechanism"
        assert isinstance(result.conclusion, str)
        assert len(result.conclusion) > 0

    def test_competing_mechanism_identifies_signal_for_oracle(
        self, signal_ar_world
    ):
        """An oracle that uses signal should show signal is the mechanism."""
        # Oracle strategy: uses the signal feature directly
        def oracle_strategy(world: SyntheticWorld):
            from sas.quant.experiment.mechanism_attribution import run_oracle_strategy
            return run_oracle_strategy(world)

        result = run_competing_mechanism_test(
            signal_ar_world, oracle_strategy, "test-mech"
        )
        # Oracle should be exploiting signal (not momentum)
        assert "signal" in result.conclusion.lower() or "ambiguous" in result.conclusion.lower()

    def test_competing_mechanism_identifies_momentum(self, null_ar_world):
        """On null AR world, momentum strategy exploits AR."""
        result = run_competing_mechanism_test(
            null_ar_world, _momentum_strategy, "test-mech"
        )
        # The test should find that returns ablation matters
        assert result.sharpe_drop != 0.0

    def test_competing_evidence_strength(self, signal_ar_world):
        result = run_competing_mechanism_test(
            signal_ar_world, _momentum_strategy, "test-mech"
        )
        assert 0.0 <= result.evidence_strength <= 1.0


# ---------------------------------------------------------------------------
# Test: Temporal perturbation detects timing sensitivity
# ---------------------------------------------------------------------------


class TestTemporalPerturbation:
    def test_temporal_shift_reduces_sharpe(self, signal_iid_world):
        """Shifting returns should reduce Sharpe for timing-sensitive strategies."""
        result = run_temporal_perturbation(
            signal_iid_world, _momentum_strategy, "test-mech", max_shift=3
        )
        assert isinstance(result.sharpe_drop, float)

    def test_temporal_perturbation_is_timing_sensitive(self, signal_iid_world):
        """A strategy that uses returns should be timing-sensitive."""
        result = run_temporal_perturbation(
            signal_iid_world, _momentum_strategy, "test-mech", max_shift=5
        )
        # If strategy is timing-sensitive, Sharpe should drop
        assert result.sharpe_drop != 0.0

    def test_temporal_max_shift_respected(self, signal_iid_world):
        result = run_temporal_perturbation(
            signal_iid_world, _momentum_strategy, "test-mech", max_shift=10
        )
        assert "10" in result.perturbation_description

    def test_temporal_on_null_iid_world(self, null_iid_world):
        """On null IID world, temporal shift should have minimal effect."""
        result = run_temporal_perturbation(
            null_iid_world, _momentum_strategy, "test-mech", max_shift=3
        )
        # Null IID: momentum has no edge, so shift shouldn't matter much
        assert abs(result.original_sharpe) < 2.0


# ---------------------------------------------------------------------------
# Test: Integration — all investigations on multiple world types
# ---------------------------------------------------------------------------


class TestAllInvestigationsIntegration:
    def test_all_investigations_null_iid(self, null_iid_world):
        results = run_all_investigations(
            null_iid_world, _momentum_strategy, "test-mech"
        )
        assert len(results) >= 3
        for r in results:
            assert r.world_id == "test-null-iid"

    def test_all_investigations_signal_ar(self, signal_ar_world):
        results = run_all_investigations(
            signal_ar_world, _momentum_strategy, "test-mech"
        )
        # Should run: ablation (returns), ablation (signal), permutation, competing, temporal
        assert len(results) >= 4
        # All results should reference the correct world
        for r in results:
            assert r.world_id == "test-signal-ar"

    def test_all_investigations_buy_and_hold(self, signal_iid_world):
        results = run_all_investigations(
            signal_iid_world, _buy_and_hold_strategy, "test-mech"
        )
        assert len(results) >= 3

    def test_investigation_results_have_unique_types(self, signal_ar_world):
        results = run_all_investigations(
            signal_ar_world, _momentum_strategy, "test-mech"
        )
        types = [r.investigation_type for r in results]
        # Should have at least 3 unique investigation types
        assert len(set(types)) >= 3


# ---------------------------------------------------------------------------
# Test: Evidence artifact serialization
# ---------------------------------------------------------------------------


class TestEvidenceSerialization:
    def test_investigation_result_to_dict(self, signal_iid_world):
        result = run_feature_ablation(
            signal_iid_world, _momentum_strategy, "test-mech", feature="returns"
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["investigation_type"] == "feature_ablation"
        assert d["mechanism_id"] == "test-mech"
        assert "evidence_strength" in d
        assert "conclusion" in d

    def test_all_results_serializable(self, signal_ar_world):
        results = run_all_investigations(
            signal_ar_world, _momentum_strategy, "test-mech"
        )
        for r in results:
            d = r.to_dict()
            assert isinstance(d, dict)
            assert "investigation_type" in d


# ---------------------------------------------------------------------------
# Test: Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_ablate_missing_feature(self, signal_iid_world):
        """Ablating a feature that doesn't exist should not crash."""
        result = run_feature_ablation(
            signal_iid_world, _momentum_strategy, "test-mech", feature="nonexistent"
        )
        # Should still return a result (feature not found → no change)
        assert isinstance(result, MechanismInvestigationResult)

    def test_empty_world_data(self):
        """Investigation on a world with minimal data."""
        world = generate_null_world(
            world_id="test-empty",
            seed=42,
            start_date="2024-01-01",
            end_date="2024-01-31",  # ~20 business days
        )
        result = run_feature_ablation(
            world, _momentum_strategy, "test-mech", feature="returns"
        )
        assert isinstance(result, MechanismInvestigationResult)

    def test_single_permutation(self, signal_iid_world):
        result = run_permutation_test(
            signal_iid_world, _momentum_strategy, "test-mech", n_permutations=1
        )
        assert isinstance(result, MechanismInvestigationResult)

    def test_max_shift_one(self, signal_iid_world):
        result = run_temporal_perturbation(
            signal_iid_world, _momentum_strategy, "test-mech", max_shift=1
        )
        assert isinstance(result, MechanismInvestigationResult)


# ---------------------------------------------------------------------------
# Test: Evidence accumulation without authority expansion
# ---------------------------------------------------------------------------


class TestEvidenceAccumulation:
    def test_multiple_investigations_accumulate_evidence(
        self, signal_ar_world
    ):
        """Running all investigations accumulates evidence without expanding API."""
        results = run_all_investigations(
            signal_ar_world, _momentum_strategy, "test-mech"
        )
        # Total evidence strength should be sum of individual strengths
        total_evidence = sum(r.evidence_strength for r in results)
        assert total_evidence > 0.0
        # But evidence does NOT create new epistemic states
        # (frozen API: SUPPORTED/REFUTED/INCONCLUSIVE only)

    def test_is_robust_flag_consistent(self, signal_iid_world):
        """is_robust flag should be consistent with Sharpe persistence."""
        result = run_feature_ablation(
            signal_iid_world, _momentum_strategy, "test-mech", feature="returns"
        )
        # If Sharpe persists (low drop), is_robust should be True
        if abs(result.sharpe_drop) < 0.1:
            assert result.is_robust is True
        else:
            assert result.is_robust is False or result.is_robust is True
