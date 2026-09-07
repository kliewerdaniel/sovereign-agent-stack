"""Unit tests for the temporal authority and research window."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from sas.quant.research.temporal import (
    ExecutionCapability,
    HoldoutWindow,
    ResearchWindow,
    TemporalAuthority,
)


class TestResearchWindow:
    """Test the immutable research window."""

    def setup_method(self):
        self.window = ResearchWindow(
            earliest_timestamp="2024-01-01",
            max_permitted_timestamp="2024-09-30",
            holdout_start="2024-10-01",
            final_timestamp="2024-12-31",
        )

    def test_valid_date_range(self):
        is_valid, error = self.window.validate_date_range("2024-01-01", "2024-09-30")
        assert is_valid
        assert error == ""

    def test_date_range_within_window(self):
        is_valid, error = self.window.validate_date_range("2024-03-01", "2024-06-30")
        assert is_valid

    def test_date_range_exceeds_max(self):
        is_valid, error = self.window.validate_date_range("2024-01-01", "2024-12-31")
        assert not is_valid
        assert "exceeds maximum permitted" in error

    def test_date_range_before_earliest(self):
        is_valid, error = self.window.validate_date_range("2023-01-01", "2024-06-30")
        assert not is_valid
        assert "before earliest available" in error

    def test_start_beyond_max(self):
        is_valid, error = self.window.validate_date_range("2024-11-01", "2024-12-31")
        assert not is_valid
        assert "beyond the research window" in error

    def test_empty_dates(self):
        is_valid, error = self.window.validate_date_range("", "")
        assert is_valid


class TestHoldoutWindow:
    def setup_method(self):
        self.window = HoldoutWindow(
            holdout_start="2024-10-01",
            final_timestamp="2024-12-31",
        )

    def test_valid_holdout_range(self):
        is_valid, error = self.window.validate_date_range("2024-10-01", "2024-12-31")
        assert is_valid

    def test_holdout_cannot_access_research_data(self):
        is_valid, error = self.window.validate_date_range("2024-01-01", "2024-09-30")
        assert not is_valid
        assert "cannot access data before" in error


class TestTemporalAuthority:
    def setup_method(self):
        self.authority = TemporalAuthority(
            research_window=ResearchWindow(
                earliest_timestamp="2024-01-01",
                max_permitted_timestamp="2024-09-30",
                holdout_start="2024-10-01",
                final_timestamp="2024-12-31",
            ),
            holdout_window=HoldoutWindow(
                holdout_start="2024-10-01",
                final_timestamp="2024-12-31",
            ),
        )

    def test_initial_capability_is_research(self):
        assert self.authority.capability == ExecutionCapability.RESEARCH

    def test_research_validation(self):
        is_valid, error = self.authority.validate_date_range("2024-01-01", "2024-09-30")
        assert is_valid

    def test_research_cannot_access_holdout(self):
        is_valid, error = self.authority.validate_date_range("2024-10-01", "2024-12-31")
        assert not is_valid

    def test_transition_to_holdout(self):
        self.authority.transition_to_holdout()
        assert self.authority.capability == ExecutionCapability.HOLDOUT

    def test_holdout_validation(self):
        self.authority.transition_to_holdout()
        is_valid, error = self.authority.validate_date_range("2024-10-01", "2024-12-31")
        assert is_valid

    def test_holdout_cannot_access_research(self):
        self.authority.transition_to_holdout()
        is_valid, error = self.authority.validate_date_range("2024-01-01", "2024-09-30")
        assert not is_valid

    def test_transition_to_final(self):
        self.authority.transition_to_holdout()
        self.authority.transition_to_final()
        assert self.authority.capability == ExecutionCapability.FINAL

    def test_final_has_no_data_access(self):
        self.authority.transition_to_holdout()
        self.authority.transition_to_final()
        is_valid, error = self.authority.validate_date_range("2024-01-01", "2024-12-31")
        assert not is_valid
        assert "No market data access" in error

    def test_no_transition_back_to_research(self):
        self.authority.transition_to_holdout()
        with pytest.raises(ValueError, match="Cannot transition to HOLDOUT from holdout"):
            self.authority.transition_to_holdout()

    def test_no_skip_to_final(self):
        with pytest.raises(ValueError, match="Cannot transition to FINAL from research"):
            self.authority.transition_to_final()

    def test_one_way_transitions(self):
        self.authority.transition_to_holdout()
        self.authority.transition_to_final()
        with pytest.raises(ValueError):
            self.authority.transition_to_holdout()  # Can't go back
