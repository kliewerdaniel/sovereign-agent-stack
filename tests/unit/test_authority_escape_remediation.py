"""Phase 26 tests: Authority Escape Remediation.

Tests verify that the six open effects from Phase 25 can be grouped
by architectural cause and remediated by introducing enforcement
at architectural boundaries.
"""

import pytest
from examples.sovereign_agent.authority_escape_remediation import (
    ArchitecturalCause,
    RemediationEngine,
    RemediationPlan,
    RemediationStatus,
    run_all_phase26_experiments,
)


class TestRemediationEngine:
    """Test remediation engine."""

    def test_analyze_and_plan(self):
        engine = RemediationEngine()
        plans = engine.analyze_and_plan()
        assert len(plans) == 4

    def test_apply_remediation(self):
        engine = RemediationEngine()
        plans = engine.analyze_and_plan()
        applied = engine.apply_remediation(plans[0])
        assert applied.status == RemediationStatus.APPLIED

    def test_verify_remediation(self):
        engine = RemediationEngine()
        plans = engine.analyze_and_plan()
        applied = engine.apply_remediation(plans[0])
        verified = engine.verify_remediation(applied)
        assert verified is True

    def test_test_bypass(self):
        engine = RemediationEngine()
        plans = engine.analyze_and_plan()
        applied = engine.apply_remediation(plans[0])
        bypass_detected = engine.test_bypass(applied)
        assert bypass_detected is True


class TestRemediationPlans:
    """Test remediation plans."""

    def test_plan_argo_gate(self):
        engine = RemediationEngine()
        plans = engine.analyze_and_plan()
        argo_plans = [p for p in plans if p.architectural_cause == ArchitecturalCause.MISSING_RUNTIME_GATE]
        assert len(argo_plans) == 1
        assert "subprocess_001" in argo_plans[0].affected_effects
        assert "identity_001" in argo_plans[0].affected_effects

    def test_plan_filesystem(self):
        engine = RemediationEngine()
        plans = engine.analyze_and_plan()
        fs_plans = [p for p in plans if p.architectural_cause == ArchitecturalCause.MISSING_FILESYSTEM_BOUND]
        assert len(fs_plans) == 1
        assert "filesystem_001" in fs_plans[0].affected_effects
        assert "filesystem_002" in fs_plans[0].affected_effects

    def test_plan_database(self):
        engine = RemediationEngine()
        plans = engine.analyze_and_plan()
        db_plans = [p for p in plans if p.architectural_cause == ArchitecturalCause.MISSING_DATABASE_BOUND]
        assert len(db_plans) == 1
        assert "database_001" in db_plans[0].affected_effects

    def test_plan_subprocess(self):
        engine = RemediationEngine()
        plans = engine.analyze_and_plan()
        sp_plans = [p for p in plans if p.architectural_cause == ArchitecturalCause.MISSING_SUBPROCESS_BOUND]
        assert len(sp_plans) == 1
        assert "subprocess_002" in sp_plans[0].affected_effects


class TestAllPhase26Experiments:
    """Test all Phase 26 experiments."""

    def test_all_experiments_run(self):
        results = run_all_phase26_experiments()
        assert results["total_plans"] == 4

    def test_total_affected_effects(self):
        results = run_all_phase26_experiments()
        assert results["total_affected_effects"] == 6

    def test_applied_count(self):
        results = run_all_phase26_experiments()
        assert results["applied_count"] == 4

    def test_verified_count(self):
        results = run_all_phase26_experiments()
        assert results["verified_count"] == 4

    def test_bypass_detected_count(self):
        results = run_all_phase26_experiments()
        assert results["bypass_detected_count"] == 4

    def test_architectural_causes(self):
        results = run_all_phase26_experiments()
        assert len(results["architectural_causes"]) == 4
        assert "missing_runtime_gate" in results["architectural_causes"]
        assert "missing_filesystem_bound" in results["architectural_causes"]
        assert "missing_database_bound" in results["architectural_causes"]
        assert "missing_subprocess_bound" in results["architectural_causes"]


class TestRemediationPlan:
    """Test remediation plan."""

    def test_plan_creation(self):
        plan = RemediationPlan(
            plan_id="test",
            architectural_cause=ArchitecturalCause.MISSING_RUNTIME_GATE,
            description="Test",
            affected_effects=["test_001"],
            enforcement_boundary="RuntimeAuthorityGate",
            remediation_steps=["step1", "step2"],
        )
        assert plan.status == RemediationStatus.PLANNED

    def test_plan_with_argo_effects(self):
        plan = RemediationPlan(
            plan_id="test",
            architectural_cause=ArchitecturalCause.MISSING_RUNTIME_GATE,
            description="Test",
            affected_effects=["subprocess_001", "identity_001"],
            enforcement_boundary="RuntimeAuthorityGate",
            remediation_steps=["step1"],
        )
        assert len(plan.affected_effects) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
