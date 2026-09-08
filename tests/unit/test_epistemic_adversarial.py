"""Tests for Epistemic Sovereignty Adversarial Suite."""

from __future__ import annotations

import pytest

from sas.quant.experiment.epistemic_adversarial import (
    AttackResult,
    AttackType,
    BoundaryType,
    attack_high_sharpe,
    attack_massive_sample,
    attack_huge_search_budget,
    attack_irrelevant_evidence,
    attack_correct_hypothesis_invalid_experiment,
    attack_valid_experiment_non_identifiable,
    attack_correct_mechanism_insufficient_authority,
    attack_dgp_oracle_leakage,
    attack_agent_confidence,
    attack_holdout_performance,
    attack_convergent_non_discriminative,
    attack_conflicting_evidence,
    run_adversarial_suite,
    generate_adversarial_report,
)


# ---------------------------------------------------------------------------
# Test: Individual Attacks
# ---------------------------------------------------------------------------


class TestAttack1_HighSharpe:
    def test_blocked(self):
        result = attack_high_sharpe()
        assert result.blocked
        assert result.authority_not_granted

    def test_blocked_at_proposition(self):
        result = attack_high_sharpe()
        assert result.blocked_at in [BoundaryType.PROPOSITION, BoundaryType.EPISTEMIC_EVALUATOR]


class TestAttack2_MassiveSample:
    def test_blocked(self):
        result = attack_massive_sample()
        assert result.blocked
        assert result.authority_not_granted

    def test_blocked_at_design(self):
        result = attack_massive_sample()
        assert result.blocked_at == BoundaryType.EXPERIMENTAL_DESIGN


class TestAttack3_HugeSearchBudget:
    def test_blocked(self):
        result = attack_huge_search_budget()
        assert result.blocked
        assert result.authority_not_granted


class TestAttack4_IrrelevantEvidence:
    def test_blocked(self):
        result = attack_irrelevant_evidence()
        assert result.blocked
        assert result.authority_not_granted

    def test_blocked_at_proposition(self):
        result = attack_irrelevant_evidence()
        assert result.blocked_at == BoundaryType.PROPOSITION


class TestAttack5_CorrectHypothesisInvalidExperiment:
    def test_blocked(self):
        result = attack_correct_hypothesis_invalid_experiment()
        assert result.blocked
        assert result.authority_not_granted

    def test_blocked_at_design(self):
        result = attack_correct_hypothesis_invalid_experiment()
        assert result.blocked_at == BoundaryType.EXPERIMENTAL_DESIGN


class TestAttack6_ValidExperimentNonIdentifiable:
    def test_blocked(self):
        result = attack_valid_experiment_non_identifiable()
        assert result.blocked
        assert result.authority_not_granted


class TestAttack7_CorrectMechanismInsufficientAuthority:
    def test_blocked(self):
        result = attack_correct_mechanism_insufficient_authority()
        assert result.blocked
        assert result.authority_not_granted


class TestAttack8_DGPOracleLeakage:
    def test_blocked(self):
        result = attack_dgp_oracle_leakage()
        assert result.blocked
        assert result.authority_not_granted

    def test_blocked_at_evaluator(self):
        result = attack_dgp_oracle_leakage()
        assert result.blocked_at == BoundaryType.EPISTEMIC_EVALUATOR


class TestAttack9_AgentConfidence:
    def test_blocked(self):
        result = attack_agent_confidence()
        assert result.blocked
        assert result.authority_not_granted


class TestAttack10_HoldoutPerformance:
    def test_blocked(self):
        result = attack_holdout_performance()
        assert result.blocked
        assert result.authority_not_granted


class TestAttack11_ConvergentNonDiscriminative:
    def test_blocked(self):
        result = attack_convergent_non_discriminative()
        assert result.blocked
        assert result.authority_not_granted


class TestAttack12_ConflictingEvidence:
    def test_blocked(self):
        result = attack_conflicting_evidence()
        assert result.blocked
        assert result.authority_not_granted


# ---------------------------------------------------------------------------
# Test: Full Suite
# ---------------------------------------------------------------------------


class TestAdversarialSuite:
    def test_all_attacks_blocked(self):
        results = run_adversarial_suite()
        assert len(results) == 12
        for r in results:
            assert r.blocked, f"Attack {r.attack_type.value} was NOT blocked"
            assert r.authority_not_granted

    def test_suite_has_all_attack_types(self):
        results = run_adversarial_suite()
        attack_types = {r.attack_type for r in results}
        expected = {
            AttackType.HIGH_SHARPE,
            AttackType.MASSIVE_SAMPLE,
            AttackType.HUGE_SEARCH_BUDGET,
            AttackType.IRRELEVANT_EVIDENCE,
            AttackType.CORRECT_HYPOTHESIS_INVALID_EXPERIMENT,
            AttackType.VALID_EXPERIMENT_NON_IDENTIFIABLE,
            AttackType.CORRECT_MECHANISM_INSUFFICIENT_AUTHORITY,
            AttackType.DGP_ORACLE_LEAKAGE,
            AttackType.AGENT_CONFIDENCE,
            AttackType.HOLDOUT_PERFORMANCE,
            AttackType.CONVERGENT_NON_DISCRIMINATIVE,
            AttackType.CONFLICTING_EVIDENCE,
        }
        assert attack_types == expected

    def test_report_generation(self):
        results = run_adversarial_suite()
        report = generate_adversarial_report(results)
        assert "Epistemic Sovereignty Adversarial Suite" in report
        assert "Blocked: 12" in report or "**Blocked:** 12" in report

    def test_boundary_coverage(self):
        results = run_adversarial_suite()
        boundaries = {r.blocked_at for r in results if r.blocked}
        # Should cover multiple boundaries
        assert len(boundaries) >= 3
