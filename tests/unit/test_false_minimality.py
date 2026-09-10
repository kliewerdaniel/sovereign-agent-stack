"""Phase 3 tests: False Minimality.

Tests whether the existing completeness semantics can distinguish:
- "Nothing is affected" (empty frontier + complete graph)
- "Nothing affected has been established" (empty frontier + incomplete graph)
"""

import pytest
from examples.sovereign_agent.dependency_completeness import (
    CompletenessMethod,
    CompletenessStatus,
    IntersectionStatus,
    create_completeness_scope,
)
from examples.sovereign_agent.false_minimality_experiment import (
    analyze_completeness_semantics,
    run_false_minimality_matrix,
)
from examples.sovereign_agent.revalidation_experiment import (
    FrontierClassification,
    FrontierSoundness,
)


class TestFalseMinimality:
    """Tests for false-minimality detection."""

    def test_complete_graph_related_mutation(self):
        """Test: complete graph + related mutation = frontier finds dependency."""
        results = run_false_minimality_matrix()
        r = next(r for r in results if r.test_name == "complete_graph_related_mutation")

        assert r.completeness_status == CompletenessStatus.KNOWN_COMPLETE
        assert r.intersection_status == IntersectionStatus.INTERSECTION_FOUND
        assert r.frontier_classification == FrontierClassification.EXACT
        assert r.soundness == FrontierSoundness.SOUND

    def test_incomplete_graph_undeclared_mutation(self):
        """Test: incomplete graph + undeclared mutation = empty frontier BUT cannot conclude."""
        results = run_false_minimality_matrix()
        r = next(r for r in results if r.test_name == "incomplete_graph_undeclared_mutation")

        # The critical false-minimality case
        assert r.completeness_status == CompletenessStatus.KNOWN_INCOMPLETE
        assert r.intersection_status == IntersectionStatus.NO_INTERSECTION_ESTABLISHED
        assert not r.computed_frontier  # Empty frontier
        assert r.frontier_classification == FrontierClassification.UNDER_APPROXIMATED
        assert r.soundness == FrontierSoundness.UNSOUND

    def test_complete_graph_unrelated_mutation(self):
        """Test: complete graph + unrelated mutation = empty frontier is trustworthy."""
        results = run_false_minimality_matrix()
        r = next(r for r in results if r.test_name == "complete_graph_unrelated_mutation")

        assert r.completeness_status == CompletenessStatus.KNOWN_COMPLETE
        assert r.intersection_status == IntersectionStatus.NO_RELEVANT_DEPENDENCY_EXISTS
        assert not r.computed_frontier  # Empty frontier
        assert r.frontier_classification == FrontierClassification.EXACT
        assert r.soundness == FrontierSoundness.SOUND

    def test_incomplete_graph_unrelated_mutation(self):
        """Test: incomplete graph + unrelated mutation = empty frontier is unknown."""
        results = run_false_minimality_matrix()
        r = next(r for r in results if r.test_name == "incomplete_graph_unrelated_mutation")

        assert r.completeness_status == CompletenessStatus.KNOWN_INCOMPLETE
        assert r.intersection_status == IntersectionStatus.NO_INTERSECTION_ESTABLISHED
        assert not r.computed_frontier  # Empty frontier
        # Cannot establish irrelevance with incomplete graph
        assert r.soundness == FrontierSoundness.UNKNOWN

    def test_completeness_semantics_are_sufficient(self):
        """Test: existing completeness semantics can distinguish the cases."""
        results = run_false_minimality_matrix()
        analysis = analyze_completeness_semantics(results)

        # The key finding: intersection distinction works
        assert analysis["intersection_distinction_works"] is True
        assert not analysis["missing_semantics"]

    def test_empty_frontier_meaning_depends_on_completeness(self):
        """Test: empty frontier has different meaning depending on completeness."""
        results = run_false_minimality_matrix()

        # Find empty-frontier cases
        empty_frontier_results = [r for r in results if not r.computed_frontier]

        # Should have at least 2 empty-frontier cases
        assert len(empty_frontier_results) >= 2

        # They should have different completeness statuses
        completeness_statuses = {r.completeness_status for r in empty_frontier_results}
        assert len(completeness_statuses) > 1

        # They should have different intersection statuses
        intersection_statuses = {r.intersection_status for r in empty_frontier_results}
        assert len(intersection_statuses) > 1

    def test_no_automatic_preserve_from_empty_frontier(self):
        """Test: empty frontier does NOT automatically mean PRESERVE."""
        results = run_false_minimality_matrix()

        # The critical false-minimality case
        r = next(r for r in results if r.test_name == "incomplete_graph_undeclared_mutation")

        # Empty frontier + incomplete graph ≠ PRESERVE
        # The protocol must NOT conclude "no revalidation required"
        assert r.intersection_status != IntersectionStatus.NO_RELEVANT_DEPENDENCY_EXISTS
        assert r.completeness_status != CompletenessStatus.KNOWN_COMPLETE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
