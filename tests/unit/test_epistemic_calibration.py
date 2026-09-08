"""Tests for Epistemic Authority Calibration."""

from __future__ import annotations

import pytest

from sas.quant.experiment.epistemic_calibration import (
    CalibrationLevel,
    LevelSpec,
    CalibrationResult,
    LevelSummary,
    LEVEL_SPECS,
    run_single_trial,
    run_epistemic_calibration,
    generate_calibration_report,
)


# ---------------------------------------------------------------------------
# Test: Level Specifications
# ---------------------------------------------------------------------------


class TestLevelSpecs:
    def test_six_levels(self):
        assert len(LEVEL_SPECS) == 6

    def test_level_values(self):
        levels = [s.level for s in LEVEL_SPECS]
        assert levels == [
            CalibrationLevel.IMPOSSIBLE,
            CalibrationLevel.OBSERVABLE,
            CalibrationLevel.IDENTIFIABLE,
            CalibrationLevel.REPLICATED,
            CalibrationLevel.GENERALIZED,
            CalibrationLevel.AUTHORIZED,
        ]

    def test_impossible_has_confounders(self):
        spec = LEVEL_SPECS[0]
        assert spec.dgp_params["has_signal"] is True
        assert spec.dgp_params["autocorrelation"] > 0

    def test_authorized_has_strong_signal(self):
        spec = LEVEL_SPECS[-1]
        assert spec.dgp_params["signal_strength"] >= 0.8
        assert spec.dgp_params["autocorrelation"] == 0.0
        assert spec.has_holdout is True

    def test_authorized_expects_supported(self):
        spec = LEVEL_SPECS[-1]
        assert spec.expected_status == "supported"

    def test_impossible_expects_inconclusive(self):
        spec = LEVEL_SPECS[0]
        assert spec.expected_status == "inconclusive"


# ---------------------------------------------------------------------------
# Test: Single Trial
# ---------------------------------------------------------------------------


class TestSingleTrial:
    def test_impossible_trial(self):
        spec = LEVEL_SPECS[0]
        result = run_single_trial(spec, seed=42)
        assert result.level == CalibrationLevel.IMPOSSIBLE
        assert result.expected_status == "inconclusive"

    def test_authorized_trial(self):
        spec = LEVEL_SPECS[-1]
        result = run_single_trial(spec, seed=42)
        assert result.level == CalibrationLevel.AUTHORIZED
        assert result.expected_status == "supported"

    def test_trial_has_world_id(self):
        spec = LEVEL_SPECS[0]
        result = run_single_trial(spec, seed=42)
        assert result.world_id.startswith("cal_")

    def test_trial_has_proposition_id(self):
        spec = LEVEL_SPECS[0]
        result = run_single_trial(spec, seed=42)
        assert result.proposition_id.startswith("prop_")


# ---------------------------------------------------------------------------
# Test: Full Calibration
# ---------------------------------------------------------------------------


class TestEpistemicCalibration:
    def test_runs_all_levels(self):
        summaries = run_epistemic_calibration()
        assert len(summaries) == 6

    def test_level_names(self):
        summaries = run_epistemic_calibration()
        names = [s.name for s in summaries]
        assert names == [
            "impossible",
            "observable",
            "identifiable",
            "replicated",
            "generalized",
            "authorized",
        ]

    def test_total_trials(self):
        summaries = run_epistemic_calibration()
        total = sum(s.n_trials for s in summaries)
        # 1 + 1 + 9 + 25 + 25 + 100 = 161
        assert total == 161

    def test_authorized_has_true_positives(self):
        summaries = run_epistemic_calibration()
        authorized_summary = summaries[-1]
        n_supported = sum(
            1 for st in authorized_summary.actual_statuses if st == "supported"
        )
        assert n_supported > 0

    def test_impossible_has_no_false_positives(self):
        summaries = run_epistemic_calibration()
        impossible_summary = summaries[0]
        n_supported = sum(
            1 for st in impossible_summary.actual_statuses if st == "supported"
        )
        assert n_supported == 0


# ---------------------------------------------------------------------------
# Test: Report Generation
# ---------------------------------------------------------------------------


class TestCalibrationReport:
    def test_report_generation(self):
        summaries = run_epistemic_calibration()
        report = generate_calibration_report(summaries)
        assert "Epistemic Authority Calibration Report" in report
        assert "Monotonicity Check" in report

    def test_report_has_all_levels(self):
        summaries = run_epistemic_calibration()
        report = generate_calibration_report(summaries)
        for spec in LEVEL_SPECS:
            assert spec.name in report

    def test_report_has_key_questions(self):
        summaries = run_epistemic_calibration()
        report = generate_calibration_report(summaries)
        assert "Key Questions" in report
        assert "false positive" in report
        assert "true positive" in report


# ---------------------------------------------------------------------------
# Test: Monotonicity
# ---------------------------------------------------------------------------


class TestMonotonicity:
    def test_supported_rate_non_decreasing(self):
        summaries = run_epistemic_calibration()
        supported_rates = []
        for s in summaries:
            n_supported = sum(1 for st in s.actual_statuses if st == "supported")
            rate = n_supported / s.n_trials if s.n_trials > 0 else 0.0
            supported_rates.append(rate)

        # The supported rate should be non-decreasing
        for i in range(len(supported_rates) - 1):
            assert supported_rates[i] <= supported_rates[i + 1] + 0.01  # small tolerance
