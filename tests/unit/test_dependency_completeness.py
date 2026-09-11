"""Adversarial tests for Dependency Completeness Authority.

Tests whether the protocol can correctly reason about dependency completeness
across multiple dimensions and edge cases.
"""

import pytest
from research.examples.sovereign_agent.dependency_completeness import (
    CompletenessAssessment,
    CompletenessClaim,
    CompletenessDimension,
    CompletenessEngine,
    CompletenessMethod,
    CompletenessScope,
    CompletenessStatus,
    DimensionCoverage,
    IntersectionStatus,
    create_completeness_scope,
)
from research.examples.sovereign_agent.completeness_experiment import (
    CompletenessExperiment,
    ExperimentalCondition,
    WorldDependency,
    WorldDependencyState,
    WorldState,
    build_completeness_experiment,
    build_world_with_dependencies,
)


class TestCompletenessEngine:
    """Tests for the completeness engine."""

    def test_complete_graph(self):
        """Test assessment of a complete dependency graph."""
        engine = CompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")
        assessment = engine.assess_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["ev_001", "ev_002", "mech_001"],
            actual_dependencies=["ev_001", "ev_002", "mech_001"],
            scope=scope,
            method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
        )
        assert assessment.overall_status == CompletenessStatus.KNOWN_COMPLETE
        assert not assessment.gaps

    def test_missing_direct_dependency(self):
        """Test detection of missing direct dependency."""
        engine = CompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")
        assessment = engine.assess_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["ev_001"],
            actual_dependencies=["ev_001", "ev_002"],
            scope=scope,
            method=CompletenessMethod.STATIC_ANALYSIS_DERIVED,
        )
        assert assessment.overall_status in (
            CompletenessStatus.KNOWN_INCOMPLETE,
            CompletenessStatus.UNKNOWN,
            CompletenessStatus.CONDITIONAL_COMPLETENESS,
        )
        assert "ev_002" in assessment.gaps

    def test_over_broad_dependency(self):
        """Test detection of over-broad dependency graph."""
        engine = CompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")
        assessment = engine.assess_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["ev_001", "ev_002", "ev_003"],
            actual_dependencies=["ev_001"],
            scope=scope,
            method=CompletenessMethod.DOCUMENTATION_DERIVED,
        )
        assert assessment.overall_status == CompletenessStatus.OVER_APPROXIMATED

    def test_model_hypothesized_never_authoritative(self):
        """Test that model-hypothesized completeness is never authoritative."""
        engine = CompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")
        assessment = engine.assess_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["ev_001", "ev_002"],
            actual_dependencies=["ev_001", "ev_002"],
            scope=scope,
            method=CompletenessMethod.MODEL_HYPOTHESIZED,
        )
        # Model-hypothesized completeness should be untested, not known complete
        assert assessment.overall_status == CompletenessStatus.UNTESTED_COMPLETENESS
        for claim in assessment.claims:
            assert not claim.is_authoritative()

    def test_completeness_claim_not_authoritative(self):
        """Test that completeness claims are never authoritative."""
        claim = CompletenessClaim(
            claim_id="claim_001",
            authorization_id="auth_001",
            graph_id="graph_001",
            status=CompletenessStatus.KNOWN_COMPLETE,
            scope=create_completeness_scope("prop_001", "payment"),
            method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
            confidence=1.0,
        )
        assert not claim.is_authoritative()

    def test_dimension_coverage_computed(self):
        """Test that dimension coverage is computed for all dimensions."""
        engine = CompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")
        assessment = engine.assess_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["ev_001", "mech_001", "res_001"],
            actual_dependencies=["ev_001", "mech_001", "res_001", "cons_001"],
            scope=scope,
        )
        dimensions = {dc.dimension for dc in assessment.dimension_coverages}
        assert CompletenessDimension.EVIDENCE in dimensions
        assert CompletenessDimension.MECHANISM in dimensions
        assert CompletenessDimension.RESOURCE in dimensions

    def test_intersection_status_distinction(self):
        """Test that intersection status distinguishes key cases."""
        engine = CompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")

        # Case 1: Graph is complete, evidence is unrelated
        assessment_complete = engine.assess_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["ev_001", "ev_002"],
            actual_dependencies=["ev_001", "ev_002"],
            scope=scope,
            method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
        )
        status = engine.check_intersection_status(
            "ev_003", ["ev_001", "ev_002"], assessment_complete
        )
        assert status == IntersectionStatus.NO_RELEVANT_DEPENDENCY_EXISTS

        # Case 2: Graph is incomplete, evidence doesn't intersect
        assessment_incomplete = engine.assess_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["ev_001"],
            actual_dependencies=["ev_001", "ev_002"],
            scope=scope,
        )
        status = engine.check_intersection_status(
            "ev_003", ["ev_001"], assessment_incomplete
        )
        assert status == IntersectionStatus.NO_INTERSECTION_ESTABLISHED

    def test_compare_methods(self):
        """Test comparison of completeness methods."""
        engine = CompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")
        results = engine.compare_methods(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared=["ev_001", "ev_002"],
            actual=["ev_001", "ev_002", "mech_001"],
            scope=scope,
        )
        assert CompletenessMethod.MODEL_HYPOTHESIZED.value in results
        assert CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED.value in results

    def test_scope_sensitivity(self):
        """Test that completeness is scoped to proposition and consequence."""
        engine = CompletenessEngine()
        scope_payment = create_completeness_scope("prop_001", "payment")
        scope_read = create_completeness_scope("prop_001", "read_only")

        assessment_payment = engine.assess_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["ev_001"],
            actual_dependencies=["ev_001", "ev_002", "ev_003"],
            scope=scope_payment,
        )
        assessment_read = engine.assess_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["ev_001"],
            actual_dependencies=["ev_001"],
            scope=scope_read,
        )
        # Same graph may be complete for read but incomplete for payment
        assert assessment_payment.assessment_id != assessment_read.assessment_id


class TestCompletenessExperiment:
    """Tests for the experimental environment."""

    def test_experiment_runs_all_conditions(self):
        """Test that experiment runs all conditions."""
        experiment = build_completeness_experiment()
        results = experiment.run_all()
        assert len(results) == len(experiment.conditions)

    def test_complete_graph_correct(self):
        """Test that complete graph is correctly identified."""
        experiment = build_completeness_experiment()
        experiment.run_all()
        complete_results = [
            r for r in experiment.results
            if r.condition.condition_id == "complete_graph"
        ]
        assert len(complete_results) == 1
        assert complete_results[0].assessment.overall_status == CompletenessStatus.KNOWN_COMPLETE
        assert not complete_results[0].false_completeness

    def test_missing_dependency_detected(self):
        """Test that missing dependencies are detected."""
        experiment = build_completeness_experiment()
        experiment.run_all()
        missing_results = [
            r for r in experiment.results
            if r.condition.condition_id == "missing_direct"
        ]
        assert len(missing_results) == 1
        assert missing_results[0].actual_gaps  # There are actual gaps

    def test_false_completeness_detected(self):
        """Test that false completeness is detected."""
        experiment = build_completeness_experiment()
        experiment.run_all()
        false_results = [
            r for r in experiment.results
            if r.condition.condition_id == "false_completeness"
        ]
        assert len(false_results) == 1
        # The model-hypothesized method should NOT produce KNOWN_COMPLETE
        # since there's a missing mechanism dependency
        assert false_results[0].assessment.overall_status in (
            CompletenessStatus.UNTESTED_COMPLETENESS,
            CompletenessStatus.UNKNOWN,
            CompletenessStatus.KNOWN_INCOMPLETE,
        )

    def test_over_approximation_detected(self):
        """Test that over-approximation is detected."""
        experiment = build_completeness_experiment()
        experiment.run_all()
        over_results = [
            r for r in experiment.results
            if r.condition.condition_id == "over_broad"
        ]
        assert len(over_results) == 1
        assert over_results[0].assessment.overall_status == CompletenessStatus.OVER_APPROXIMATED

    def test_summary_statistics(self):
        """Test that summary statistics are computed."""
        experiment = build_completeness_experiment()
        experiment.run_all()
        summary = experiment.summary()
        assert summary["total"] > 0
        assert "correct" in summary
        assert "false_completeness" in summary
        assert "accuracy" in summary


class TestIntersectionStatus:
    """Tests for the intersection status distinction."""

    def test_no_intersection_vs_no_relevant_dependency(self):
        """Test distinguishing NO_INTERSECTION_ESTABLISHED from NO_RELEVANT_DEPENDENCY_EXISTS."""
        engine = CompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")

        # Complete graph: NO_RELEVANT_DEPENDENCY_EXISTS
        complete_assessment = engine.assess_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["ev_001", "ev_002"],
            actual_dependencies=["ev_001", "ev_002"],
            scope=scope,
            method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
        )
        status = engine.check_intersection_status("ev_003", ["ev_001", "ev_002"], complete_assessment)
        assert status == IntersectionStatus.NO_RELEVANT_DEPENDENCY_EXISTS

        # Incomplete graph: NO_INTERSECTION_ESTABLISHED
        incomplete_assessment = engine.assess_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["ev_001"],
            actual_dependencies=["ev_001", "ev_002"],
            scope=scope,
        )
        status = engine.check_intersection_status("ev_003", ["ev_001"], incomplete_assessment)
        assert status == IntersectionStatus.NO_INTERSECTION_ESTABLISHED

    def test_unknown_completeness(self):
        """Test that unknown completeness produces CANNOT_DETERMINE."""
        engine = CompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")
        assessment = engine.assess_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["ev_001"],
            actual_dependencies=["ev_001", "ev_002", "mech_001"],
            scope=scope,
            method=CompletenessMethod.STATIC_ANALYSIS_DERIVED,
        )
        status = engine.check_intersection_status("ev_003", ["ev_001"], assessment)
        assert status == IntersectionStatus.CANNOT_DETERMINE


class TestAuthorityBootstrapPrevention:
    """Tests that completeness cannot bootstrap authority."""

    def test_completeness_claim_cannot_authorize(self):
        """Test that a completeness claim cannot authorize its own authorization."""
        claim = CompletenessClaim(
            claim_id="claim_001",
            authorization_id="auth_001",
            graph_id="graph_001",
            status=CompletenessStatus.KNOWN_COMPLETE,
            scope=create_completeness_scope("prop_001", "payment"),
            method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
            confidence=1.0,
        )
        assert not claim.is_authoritative()

    def test_completeness_does_not_create_capability(self):
        """Test that completeness assessment does not create execution capability."""
        engine = CompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")
        assessment = engine.assess_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["ev_001"],
            actual_dependencies=["ev_001"],
            scope=scope,
        )
        # Completeness assessment has no capability-creating fields
        assert not hasattr(assessment, "capability")
        assert not hasattr(assessment, "authorize")

    def test_model_completeness_never_increases_authority(self):
        """Test that model-generated completeness never increases authority."""
        engine = CompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")
        assessment = engine.assess_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["ev_001"],
            actual_dependencies=["ev_001"],
            scope=scope,
            method=CompletenessMethod.MODEL_HYPOTHESIZED,
        )
        # Model-hypothesized completeness is always UNTESTED at best
        assert assessment.overall_status in (
            CompletenessStatus.UNTESTED_COMPLETENESS,
            CompletenessStatus.UNKNOWN,
            CompletenessStatus.INCONCLUSIVE,
        )


class TestCompositionalCompleteness:
    """Tests for compositional completeness behavior."""

    def test_completeness_not_compositional(self):
        """Test that completeness of components doesn't imply completeness of composition."""
        engine = CompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")

        # A is complete
        assessment_a = engine.assess_completeness(
            authorization_id="auth_a",
            graph_id="graph_a",
            declared_dependencies=["ev_001"],
            actual_dependencies=["ev_001"],
            scope=scope,
            method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
        )

        # B is complete
        assessment_b = engine.assess_completeness(
            authorization_id="auth_b",
            graph_id="graph_b",
            declared_dependencies=["ev_002"],
            actual_dependencies=["ev_002"],
            scope=scope,
            method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
        )

        # A + B may not be complete (missing ev_003)
        assessment_ab = engine.assess_completeness(
            authorization_id="auth_ab",
            graph_id="graph_ab",
            declared_dependencies=["ev_001", "ev_002"],
            actual_dependencies=["ev_001", "ev_002", "ev_003"],
            scope=scope,
            method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
        )

        assert assessment_a.overall_status == CompletenessStatus.KNOWN_COMPLETE
        assert assessment_b.overall_status == CompletenessStatus.KNOWN_COMPLETE
        assert assessment_ab.overall_status != CompletenessStatus.KNOWN_COMPLETE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
