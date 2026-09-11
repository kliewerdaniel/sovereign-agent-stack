"""Phase 4 tests: Frontier Soundness.

Tests whether protocol classifications match experimental ground truth.
"""

import pytest
from research.examples.sovereign_agent.dependency_completeness import (
    CompletenessStatus,
    IntersectionStatus,
)
from research.examples.sovereign_agent.frontier_soundness_experiment import (
    analyze_soundness_results,
    run_all_frontier_soundness_experiments,
)
from research.examples.sovereign_agent.revalidation_experiment import (
    FrontierClassification,
    FrontierSoundness,
)


class TestFrontierSoundness:
    """Tests for frontier soundness classification."""

    def test_world_a_exact_graph(self):
        """World A: Exact graph but frontier misses downstream artifacts."""
        results = run_all_frontier_soundness_experiments()
        r = next(r for r in results if r.world_name == "A")

        assert r.completeness_status == CompletenessStatus.KNOWN_COMPLETE
        assert r.intersection_status == IntersectionStatus.INTERSECTION_FOUND
        # Protocol says exact, but experimental says under-approximated
        # This is the false-sound case
        assert r.protocol_classification == FrontierClassification.EXACT
        assert r.experimental_classification == FrontierClassification.UNDER_APPROXIMATED
        assert r.experimental_soundness == FrontierSoundness.UNSOUND

    def test_world_b_safe_over_approximation(self):
        """World B: Over-approximated graph, frontier is safe."""
        results = run_all_frontier_soundness_experiments()
        r = next(r for r in results if r.world_name == "B")

        assert r.completeness_status == CompletenessStatus.KNOWN_COMPLETE
        assert r.intersection_status == IntersectionStatus.INTERSECTION_FOUND
        # Both protocol and experimental agree: exact
        assert r.protocol_classification == FrontierClassification.EXACT
        assert r.experimental_classification == FrontierClassification.EXACT
        assert r.experimental_soundness == FrontierSoundness.SOUND

    def test_world_c_unsafe_under_approximation(self):
        """World C: Under-approximated graph, frontier is unsafe."""
        results = run_all_frontier_soundness_experiments()
        r = next(r for r in results if r.world_name == "C")

        assert r.completeness_status == CompletenessStatus.KNOWN_INCOMPLETE
        assert r.intersection_status == IntersectionStatus.NO_INTERSECTION_ESTABLISHED
        # Both protocol and experimental agree: under-approximated
        assert r.protocol_classification == FrontierClassification.UNDER_APPROXIMATED
        assert r.experimental_classification == FrontierClassification.UNDER_APPROXIMATED
        assert r.protocol_soundness == FrontierSoundness.UNSOUND
        assert r.experimental_soundness == FrontierSoundness.UNSOUND

    def test_world_d_unknown(self):
        """World D: Unknown frontier due to incomplete graph."""
        results = run_all_frontier_soundness_experiments()
        r = next(r for r in results if r.world_name == "D")

        assert r.completeness_status == CompletenessStatus.KNOWN_INCOMPLETE
        assert r.intersection_status == IntersectionStatus.NO_INTERSECTION_ESTABLISHED
        # Both protocol and experimental agree: under-approximated
        assert r.protocol_classification == FrontierClassification.UNDER_APPROXIMATED
        assert r.experimental_classification == FrontierClassification.UNDER_APPROXIMATED
        assert r.experimental_soundness == FrontierSoundness.UNSOUND

    def test_false_sound_detected(self):
        """Test that World A produces a false SOUND classification.
        
        This is the critical finding: protocol says SOUND but experimental
        says UNSOUND. The frontier is correct about the dependency but
        misses downstream artifacts (propositions, authorizations, etc.).
        """
        results = run_all_frontier_soundness_experiments()
        analysis = analyze_soundness_results(results)

        # World A produces a false sound
        assert analysis["false_sound"] >= 1

    def test_protocol_correctness_rate(self):
        """Test protocol correctness rate."""
        results = run_all_frontier_soundness_experiments()
        analysis = analyze_soundness_results(results)

        # At least 3 out of 4 should be correct
        assert analysis["protocol_correct"] >= 3

    def test_no_false_unknown(self):
        """Test that there are no false UNKNOWN classifications."""
        results = run_all_frontier_soundness_experiments()
        analysis = analyze_soundness_results(results)

        # No false unknowns
        assert analysis["false_unknown"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
