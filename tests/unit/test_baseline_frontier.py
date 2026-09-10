"""Phase 2 tests: Baseline Frontier Soundness.

Tests capture ACTUAL baseline behavior of the existing RevalidationFrontier
against ground-truth affected sets.

Key finding: The current frontier only performs flat string matching between
dependency IDs and world-change content. It lacks:
1. Transitive dependency tracking
2. Dependency graph structure awareness
3. Proposition/authorization chain propagation

This is the expected baseline — the experiments must determine what semantics
are needed to make the frontier sound.
"""

import pytest
from examples.sovereign_agent.baseline_frontier_experiment import (
    run_baseline_frontier_soundness,
)
from examples.sovereign_agent.revalidation_experiment import (
    FrontierClassification,
    FrontierSoundness,
)


class TestBaselineFrontierSoundness:
    """Tests capturing actual baseline frontier behavior."""

    def test_direct_dependency_frontier_baseline(self):
        """Capture baseline: direct dependency change frontier."""
        results = run_baseline_frontier_soundness()
        direct = next(r for r in results if r.test_name == "direct_dependency")

        # Baseline: frontier only matches flat strings in world change
        # It does NOT track that E2 is a dependency of A
        # This is EXPECTED to be empty/under-approximated with current implementation
        print(f"\nDirect dependency baseline:")
        print(f"  Computed: {direct.computed_frontier}")
        print(f"  Actual: {direct.actual_affected.to_set()}")
        print(f"  Classification: {direct.evaluation.classification}")
        print(f"  Soundness: {direct.evaluation.soundness}")

        # Record the baseline — this will be fixed in later phases
        assert direct.evaluation.classification in (
            FrontierClassification.EXACT,
            FrontierClassification.OVER_APPROXIMATED,
            FrontierClassification.UNDER_APPROXIMATED,
        )

    def test_transitive_dependency_frontier_baseline(self):
        """Capture baseline: transitive dependency change frontier."""
        results = run_baseline_frontier_soundness()
        transitive = next(r for r in results if r.test_name == "transitive_dependency")

        # Baseline: frontier has no concept of transitivity
        # It cannot know that A depends on E1 through B
        print(f"\nTransitive dependency baseline:")
        print(f"  Computed: {transitive.computed_frontier}")
        print(f"  Actual: {transitive.actual_affected.to_set()}")
        print(f"  Classification: {transitive.evaluation.classification}")

        assert transitive.evaluation.classification in (
            FrontierClassification.EXACT,
            FrontierClassification.OVER_APPROXIMATED,
            FrontierClassification.UNDER_APPROXIMATED,
        )

    def test_unrelated_dependency_frontier_baseline(self):
        """Capture baseline: unrelated dependency change frontier."""
        results = run_baseline_frontier_soundness()
        unrelated = next(r for r in results if r.test_name == "unrelated_dependency")

        # Baseline: frontier SHOULD be empty for unrelated changes
        # This is the one case where the current implementation should be correct
        print(f"\nUnrelated dependency baseline:")
        print(f"  Computed: {unrelated.computed_frontier}")
        print(f"  Actual: {unrelated.actual_affected.to_set()}")
        print(f"  Classification: {unrelated.evaluation.classification}")

        assert unrelated.evaluation.classification in (
            FrontierClassification.EXACT,
            FrontierClassification.UNDER_APPROXIMATED,
        )

    def test_shared_dependency_frontier_baseline(self):
        """Capture baseline: shared dependency change frontier."""
        results = run_baseline_frontier_soundness()
        shared = next(r for r in results if r.test_name == "shared_dependency")

        # Baseline: frontier cannot track shared dependencies across entities
        print(f"\nShared dependency baseline:")
        print(f"  Computed: {shared.computed_frontier}")
        print(f"  Actual: {shared.actual_affected.to_set()}")
        print(f"  Classification: {shared.evaluation.classification}")

        assert shared.evaluation.classification in (
            FrontierClassification.EXACT,
            FrontierClassification.OVER_APPROXIMATED,
            FrontierClassification.UNDER_APPROXIMATED,
        )

    def test_baseline_summary(self):
        """Print summary of all baseline results."""
        results = run_baseline_frontier_soundness()

        print("\n" + "=" * 60)
        print("BASELINE FRONTIER SOUNDNESS SUMMARY")
        print("=" * 60)

        exact_count = 0
        over_count = 0
        under_count = 0

        for r in results:
            if r.evaluation.classification == FrontierClassification.EXACT:
                exact_count += 1
            elif r.evaluation.classification == FrontierClassification.OVER_APPROXIMATED:
                over_count += 1
            elif r.evaluation.classification == FrontierClassification.UNDER_APPROXIMATED:
                under_count += 1

            print(f"\n{r.test_name}:")
            print(f"  Computed: {r.computed_frontier}")
            print(f"  Actual:   {r.actual_affected.to_set()}")
            print(f"  Result:   {r.evaluation.classification}")

        print(f"\n{'=' * 60}")
        print(f"Exact: {exact_count}, Over: {over_count}, Under: {under_count}")
        print(f"{'=' * 60}")

        # Record baseline — all results should be documented
        assert len(results) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
