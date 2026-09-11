"""Phase 24 tests: Authority Escape Discrimination.

Tests verify that the four hypothesized authority escapes can be
discriminated as real escapes, false positives, or controlled escapes.
"""

import pytest
from research.examples.sovereign_agent.authority_escape_discrimination import (
    AuthorityEscapeDiscriminationEngine,
    AuthorityEscapeHypothesis,
    EscapeClassification,
    EscapeDiscriminationResult,
    EscapeMechanism,
    EscapeSeverity,
    EscapeType,
    run_all_phase24_experiments,
    run_subprocess_escape_experiment,
    run_http_escape_experiment,
    run_broker_escape_experiment,
    run_filesystem_escape_experiment,
    run_governed_subprocess_experiment,
    run_governed_http_experiment,
    run_governed_broker_experiment,
    run_governed_filesystem_experiment,
    run_unguarded_subprocess_experiment,
    run_unguarded_http_experiment,
)


class TestSubprocessEscape:
    """Test subprocess escape hypothesis."""

    def test_discriminated(self):
        result = run_subprocess_escape_experiment()
        assert isinstance(result, EscapeDiscriminationResult)
        assert result.hypothesis.escape_type == EscapeType.SUBPROCESS
        assert result.hypothesis.severity == EscapeSeverity.CRITICAL


class TestHttpEscape:
    """Test HTTP escape hypothesis."""

    def test_discriminated(self):
        result = run_http_escape_experiment()
        assert isinstance(result, EscapeDiscriminationResult)
        assert result.hypothesis.escape_type == EscapeType.HTTP
        assert result.hypothesis.severity == EscapeSeverity.HIGH


class TestBrokerEscape:
    """Test broker escape hypothesis."""

    def test_discriminated(self):
        result = run_broker_escape_experiment()
        assert isinstance(result, EscapeDiscriminationResult)
        assert result.hypothesis.escape_type == EscapeType.BROKER
        assert result.hypothesis.severity == EscapeSeverity.HIGH


class TestFilesystemEscape:
    """Test filesystem escape hypothesis."""

    def test_discriminated(self):
        result = run_filesystem_escape_experiment()
        assert isinstance(result, EscapeDiscriminationResult)
        assert result.hypothesis.escape_type == EscapeType.FILESYSTEM
        assert result.hypothesis.severity == EscapeSeverity.MEDIUM


class TestGovernedSubprocess:
    """Test governed subprocess call."""

    def test_controlled(self):
        result = run_governed_subprocess_experiment()
        assert result.classification == EscapeClassification.CONTROLLED
        assert result.governed is True
        assert result.authority_traceable is True


class TestGovernedHttp:
    """Test governed HTTP call."""

    def test_controlled(self):
        result = run_governed_http_experiment()
        assert result.classification == EscapeClassification.CONTROLLED
        assert result.governed is True


class TestGovernedBroker:
    """Test governed broker call."""

    def test_controlled(self):
        result = run_governed_broker_experiment()
        assert result.classification == EscapeClassification.CONTROLLED
        assert result.governed is True


class TestGovernedFilesystem:
    """Test governed filesystem call."""

    def test_controlled(self):
        result = run_governed_filesystem_experiment()
        assert result.classification == EscapeClassification.CONTROLLED
        assert result.governed is True


class TestUnguardedSubprocess:
    """Test unguarded subprocess call."""

    def test_confirmed_escape(self):
        result = run_unguarded_subprocess_experiment()
        assert result.classification == EscapeClassification.CONFIRMED_ESCAPE
        assert result.governed is False
        assert result.amplification is True


class TestUnguardedHttp:
    """Test unguarded HTTP call."""

    def test_confirmed_escape(self):
        result = run_unguarded_http_experiment()
        assert result.classification == EscapeClassification.CONFIRMED_ESCAPE
        assert result.governed is False


class TestAllPhase24Experiments:
    """Test all Phase 24 experiments."""

    def test_all_experiments_run(self):
        results = run_all_phase24_experiments()
        assert results["total_experiments"] == 10

    def test_confirmed_escapes(self):
        results = run_all_phase24_experiments()
        assert results["confirmed_escapes"] >= 2

    def test_controlled_escapes(self):
        results = run_all_phase24_experiments()
        assert results["controlled_escapes"] >= 4

    def test_discrimination_complete(self):
        """Test that all four escape types are discriminated."""
        results = run_all_phase24_experiments()
        escape_types = set()
        for r in results["results"].values():
            escape_types.add(r.hypothesis.escape_type)
        assert EscapeType.SUBPROCESS in escape_types
        assert EscapeType.HTTP in escape_types
        assert EscapeType.BROKER in escape_types
        assert EscapeType.FILESYSTEM in escape_types


class TestEscapeDiscriminationEngine:
    """Test escape discrimination engine."""

    def test_add_hypothesis(self):
        engine = AuthorityEscapeDiscriminationEngine()
        hypothesis = AuthorityEscapeHypothesis(
            hypothesis_id="test",
            escape_type=EscapeType.SUBPROCESS,
            severity=EscapeSeverity.CRITICAL,
            description="Test",
            call_path="test",
            entry_point="test",
            exit_point="test",
            instrument="test",
        )
        engine.add_hypothesis(hypothesis)
        assert len(engine.hypotheses) == 1

    def test_discriminate_controlled(self):
        engine = AuthorityEscapeDiscriminationEngine()
        hypothesis = AuthorityEscapeHypothesis(
            hypothesis_id="test",
            escape_type=EscapeType.SUBPROCESS,
            severity=EscapeSeverity.CRITICAL,
            description="Test",
            call_path="caller → authority_gate → subprocess",
            entry_point="runtime_authority_gate",
            exit_point="external_effect",
            instrument="SubprocessInstrument",
        )
        engine.add_hypothesis(hypothesis)
        result = engine.discriminate_escape(hypothesis)
        assert result.classification == EscapeClassification.CONTROLLED

    def test_discriminate_confirmed(self):
        engine = AuthorityEscapeDiscriminationEngine()
        hypothesis = AuthorityEscapeHypothesis(
            hypothesis_id="test",
            escape_type=EscapeType.SUBPROCESS,
            severity=EscapeSeverity.CRITICAL,
            description="Test",
            call_path="caller → unguarded subprocess",
            entry_point="subprocess_exec",
            exit_point="external_effect",
            instrument="SubprocessInstrument",
        )
        engine.add_hypothesis(hypothesis)
        result = engine.discriminate_escape(hypothesis)
        assert result.classification == EscapeClassification.CONFIRMED_ESCAPE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
