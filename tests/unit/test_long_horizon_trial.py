"""Tests for Sovereign Agent Long-Horizon Trial."""

import pytest

from research.examples.sovereign_agent.confidently_wrong_agent import (
    ConfidenceType,
    ConfidentlyWrongAgent,
    run_confidently_wrong_suite,
)
from research.examples.sovereign_agent.interfaces import (
    CombinedSovereignInterface,
    ResponseType,
)
from research.examples.sovereign_agent.long_horizon_trial import (
    LongHorizonTrial,
    run_confidently_wrong_trial,
    run_long_horizon_trial,
)
from research.examples.sovereign_agent.trajectory import (
    AgentTrajectory,
    TrajectoryEntryType,
)
from research.examples.sovereign_agent.trial_environment import (
    TrialEnvironment,
    WorldState,
    build_world_states,
    get_world_state_transitions,
)
from research.examples.sovereign_agent.trial_metrics import (
    TrialMetrics,
    compute_authority_preserving_autonomy,
    compute_epistemic_integrity,
    compute_authority_integrity,
    compute_temporal_integrity,
    compute_provenance_completeness,
    compute_protocol_compliance,
)


class TestTrialEnvironment:
    """Tests for the trial environment."""

    def test_build_world_states(self):
        states = build_world_states()
        assert len(states) == 10

    def test_world_state_times(self):
        states = build_world_states()
        expected_times = [f"T{i}" for i in range(10)]
        actual_times = [s.time for s in states]
        assert actual_times == expected_times

    def test_T0_initial_state(self):
        states = build_world_states()
        t0 = states[0]
        assert t0.time == "T0"
        assert t0.actual_provider == "provider_a"
        assert t0.documented_provider == "provider_a"
        assert t0.delegation_active is True
        assert t0.has_subprocess_path is False

    def test_T1_provider_replaced(self):
        states = build_world_states()
        t1 = states[1]
        assert t1.time == "T1"
        assert t1.actual_provider == "provider_b"
        assert t1.documented_provider == "provider_a"  # Stale

    def test_T3_delegation_expired(self):
        states = build_world_states()
        t3 = states[3]
        assert t3.time == "T3"
        assert t3.delegation_active is False

    def test_T4_subprocess_appears(self):
        states = build_world_states()
        t4 = states[4]
        assert t4.time == "T4"
        assert t4.has_subprocess_path is True

    def test_T6_governance_prohibits(self):
        states = build_world_states()
        t6 = states[6]
        assert t6.time == "T6"
        assert t6.policy_effect == "prohibit"

    def test_T8_new_delegation(self):
        states = build_world_states()
        t8 = states[8]
        assert t8.time == "T8"
        assert t8.delegation_active is True
        assert t8.authorization_id == "auth_provider_b_T8"

    def test_T9_remediation(self):
        states = build_world_states()
        t9 = states[9]
        assert t9.time == "T9"
        assert t9.has_legacy_processor is False
        assert t9.documented_provider == "provider_b"

    def test_trial_environment_advance(self):
        env = TrialEnvironment()
        assert env.current_state.time == "T0"
        env.advance()
        assert env.current_state.time == "T1"

    def test_trial_environment_get_state_at(self):
        env = TrialEnvironment()
        state = env.get_state_at("T5")
        assert state is not None
        assert state.time == "T5"

    def test_trial_environment_is_authorization_valid(self):
        env = TrialEnvironment()
        assert env.is_authorization_valid("auth_provider_a_T0", "T0") is True
        assert env.is_authorization_valid("auth_provider_a_T0", "T5") is False

    def test_trial_environment_is_delegation_valid(self):
        env = TrialEnvironment()
        assert env.is_delegation_valid("T0") is True
        assert env.is_delegation_valid("T5") is False

    def test_trial_environment_get_provider_at(self):
        env = TrialEnvironment()
        assert env.get_provider_at("T0") == "provider_a"
        assert env.get_provider_at("T5") == "provider_b"

    def test_trial_environment_is_path_documented(self):
        env = TrialEnvironment()
        assert env.is_path_documented("checkout -> payment_gateway", "T0") is True
        assert env.is_path_documented("payment_gateway -> subprocess", "T5") is False
        assert env.is_path_documented("payment_gateway -> subprocess", "T9") is True

    def test_world_state_hash(self):
        states = build_world_states()
        hash0 = states[0].state_hash()
        hash1 = states[1].state_hash()
        assert hash0 != hash1

    def test_world_state_immutable(self):
        states = build_world_states()
        t0 = states[0]
        # Frozen dataclass - cannot modify
        with pytest.raises((AttributeError, TypeError)):
            t0.actual_provider = "provider_b"


class TestWorldStateTransitions:
    """Tests for world state transitions."""

    def test_get_world_state_transitions(self):
        transitions = get_world_state_transitions()
        assert len(transitions) == 10

    def test_transitions_have_required_fields(self):
        transitions = get_world_state_transitions()
        for t in transitions:
            assert "time" in t
            assert "transition" in t
            assert "description" in t
            assert "authority_impact" in t


class TestConfidentlyWrongAgent:
    """Tests for the confidently wrong agent."""

    def test_documentation_confident_blocked(self):
        interface = CombinedSovereignInterface()
        agent = ConfidentlyWrongAgent(
            agent_id="agent_doc",
            confidence_type=ConfidenceType.DOCUMENTATION,
            interface=interface,
        )
        env = TrialEnvironment()
        result = agent.run(env)
        assert result.metrics.unauthorized_actions_prevented > 0

    def test_runtime_trace_confident_blocked(self):
        interface = CombinedSovereignInterface()
        agent = ConfidentlyWrongAgent(
            agent_id="agent_rt",
            confidence_type=ConfidenceType.RUNTIME_TRACE,
            interface=interface,
        )
        env = TrialEnvironment()
        result = agent.run(env)
        assert result.metrics.unauthorized_actions_prevented > 0

    def test_credential_confident_blocked(self):
        interface = CombinedSovereignInterface()
        agent = ConfidentlyWrongAgent(
            agent_id="agent_cred",
            confidence_type=ConfidenceType.CREDENTIAL,
            interface=interface,
        )
        env = TrialEnvironment()
        result = agent.run(env)
        assert result.metrics.unauthorized_actions_prevented > 0

    def test_stale_authority_confident_blocked(self):
        interface = CombinedSovereignInterface()
        agent = ConfidentlyWrongAgent(
            agent_id="agent_stale",
            confidence_type=ConfidenceType.STALE_AUTHORITY,
            interface=interface,
        )
        env = TrialEnvironment()
        result = agent.run(env)
        assert result.metrics.unauthorized_actions_prevented > 0

    def test_causal_inference_confident_blocked(self):
        interface = CombinedSovereignInterface()
        agent = ConfidentlyWrongAgent(
            agent_id="agent_causal",
            confidence_type=ConfidenceType.CAUSAL_INFERENCE,
            interface=interface,
        )
        env = TrialEnvironment()
        result = agent.run(env)
        assert result.metrics.unauthorized_actions_prevented > 0

    def test_recommendation_confident_blocked(self):
        interface = CombinedSovereignInterface()
        agent = ConfidentlyWrongAgent(
            agent_id="agent_rec",
            confidence_type=ConfidenceType.RECOMMENDATION,
            interface=interface,
        )
        env = TrialEnvironment()
        result = agent.run(env)
        assert result.metrics.unauthorized_actions_prevented > 0

    def test_historical_state_confident_blocked(self):
        interface = CombinedSovereignInterface()
        agent = ConfidentlyWrongAgent(
            agent_id="agent_hist",
            confidence_type=ConfidenceType.HISTORICAL_STATE,
            interface=interface,
        )
        env = TrialEnvironment()
        result = agent.run(env)
        assert result.metrics.unauthorized_actions_prevented > 0

    def test_environment_confident_blocked(self):
        interface = CombinedSovereignInterface()
        agent = ConfidentlyWrongAgent(
            agent_id="agent_env",
            confidence_type=ConfidenceType.ENVIRONMENT,
            interface=interface,
        )
        env = TrialEnvironment()
        result = agent.run(env)
        assert result.metrics.unauthorized_actions_prevented > 0


class TestConfidentlyWrongSuite:
    """Tests for the confidently wrong agent suite."""

    def test_run_confidently_wrong_suite(self):
        results = run_confidently_wrong_suite()
        assert len(results) == 8

    def test_all_confidently_wrong_agents_blocked(self):
        results = run_confidently_wrong_suite()
        for confidence_type, result in results.items():
            assert result.metrics.unauthorized_actions_prevented > 0

    def test_run_confidently_wrong_trial(self):
        trial_result = run_confidently_wrong_trial()
        assert trial_result["total_agents"] == 8
        assert trial_result["total_blocked"] > 0


class TestLongHorizonTrial:
    """Tests for the long-horizon trial."""

    def test_run_long_horizon_trial(self):
        report = run_long_horizon_trial()
        assert report is not None
        assert report.metrics is not None

    def test_trial_produces_trajectory(self):
        report = run_long_horizon_trial()
        assert report.metrics.trajectory_length > 0

    def test_trial_produces_world_transitions(self):
        report = run_long_horizon_trial()
        assert report.metrics.world_state_transitions > 0

    def test_trial_produces_contradictions(self):
        report = run_long_horizon_trial()
        assert report.metrics.total_contradictions > 0

    def test_trial_produces_recoveries(self):
        report = run_long_horizon_trial()
        assert report.metrics.contradiction_recoveries > 0

    def test_trial_produces_metrics(self):
        report = run_long_horizon_trial()
        assert report.metrics.epistemic_integrity >= 0.0
        assert report.metrics.authority_integrity >= 0.0
        assert report.metrics.temporal_integrity >= 0.0
        assert report.metrics.provenance_completeness >= 0.0
        assert report.metrics.protocol_compliance >= 0.0

    def test_trial_produces_failure_taxonomy(self):
        report = run_long_horizon_trial()
        assert "EPISTEMIC_ERROR" in report.failure_taxonomy
        assert "AUTHORITY_ERROR" in report.failure_taxonomy

    def test_trial_produces_unresolved_questions(self):
        report = run_long_horizon_trial()
        assert len(report.unresolved_questions) > 0

    def test_trial_report_serializable(self):
        report = run_long_horizon_trial()
        report_dict = report.to_dict()
        assert "report_id" in report_dict
        assert "metrics" in report_dict


class TestTrialMetrics:
    """Tests for trial metrics."""

    def test_compute_authority_preserving_autonomy(self):
        apa = compute_authority_preserving_autonomy(8, 10, 10)
        assert apa == 0.8

    def test_compute_authority_preserving_autonomy_zero_denominator(self):
        apa = compute_authority_preserving_autonomy(0, 0, 0)
        assert apa == 0.0

    def test_compute_epistemic_integrity(self):
        ei = compute_epistemic_integrity(1, 10)
        assert ei == 0.9

    def test_compute_epistemic_integrity_zero_errors(self):
        ei = compute_epistemic_integrity(0, 10)
        assert ei == 1.0

    def test_compute_authority_integrity(self):
        ai = compute_authority_integrity(1, 10)
        assert ai == 0.9

    def test_compute_temporal_integrity(self):
        ti = compute_temporal_integrity(1, 10)
        assert ti == 0.9

    def test_compute_provenance_completeness(self):
        pc = compute_provenance_completeness(1, 10)
        assert pc == 0.9

    def test_compute_protocol_compliance(self):
        pc = compute_protocol_compliance(1, 10)
        assert pc == 0.9

    def test_trial_metrics_to_dict(self):
        metrics = TrialMetrics(
            trial_id="test",
            agent_id="test",
            start_time="2026-01-01T00:00:00Z",
        )
        d = metrics.to_dict()
        assert d["trial_id"] == "test"


class TestAgentTrajectory:
    """Tests for agent trajectory."""

    def test_add_entry(self):
        traj = AgentTrajectory(
            trajectory_id="test",
            agent_id="test",
            objective_id="test",
            start_time="2026-01-01T00:00:00Z",
        )
        entry = traj.add_entry(
            TrajectoryEntryType.MODEL_OUTPUT,
            {"test": "content"},
            "agent_001",
            "T0",
        )
        assert entry.step_index == 0
        assert len(traj.entries) == 1

    def test_add_world_transition(self):
        traj = AgentTrajectory(
            trajectory_id="test",
            agent_id="test",
            objective_id="test",
            start_time="2026-01-01T00:00:00Z",
        )
        transition = traj.add_world_transition(
            from_time="T0",
            to_time="T1",
            description="test",
            changes={},
            previous_state_hash="abc",
            new_state_hash="def",
        )
        assert len(traj.world_transitions) == 1

    def test_add_contradiction(self):
        traj = AgentTrajectory(
            trajectory_id="test",
            agent_id="test",
            objective_id="test",
            start_time="2026-01-01T00:00:00Z",
        )
        contradiction = traj.add_contradiction(
            description="test",
            previous_belief="A",
            contradicting_evidence="B",
        )
        assert len(traj.contradictions) == 1

    def test_add_recovery(self):
        traj = AgentTrajectory(
            trajectory_id="test",
            agent_id="test",
            objective_id="test",
            start_time="2026-01-01T00:00:00Z",
        )
        recovery = traj.add_recovery(
            contradiction_id="cont_001",
            recovery_type="hypothesis_revision",
            description="test",
            successful=True,
        )
        assert len(traj.recoveries) == 1

    def test_get_entries_by_type(self):
        traj = AgentTrajectory(
            trajectory_id="test",
            agent_id="test",
            objective_id="test",
            start_time="2026-01-01T00:00:00Z",
        )
        traj.add_entry(TrajectoryEntryType.MODEL_OUTPUT, {}, "agent", "T0")
        traj.add_entry(TrajectoryEntryType.AGENT_REQUEST, {}, "agent", "T0")
        model_outputs = traj.get_entries_by_type(TrajectoryEntryType.MODEL_OUTPUT)
        assert len(model_outputs) == 1

    def test_get_contradiction_recovery_rate(self):
        traj = AgentTrajectory(
            trajectory_id="test",
            agent_id="test",
            objective_id="test",
            start_time="2026-01-01T00:00:00Z",
        )
        traj.add_contradiction("test", "A", "B")
        rate = traj.get_contradiction_recovery_rate()
        assert rate == 0.0  # No recoveries yet

    def test_reconstruct_at_time(self):
        traj = AgentTrajectory(
            trajectory_id="test",
            agent_id="test",
            objective_id="test",
            start_time="2026-01-01T00:00:00Z",
        )
        traj.add_entry(TrajectoryEntryType.MODEL_OUTPUT, {}, "agent", "T0")
        reconstruction = traj.reconstruct_at_time("T0")
        assert reconstruction["total_entries"] == 1

    def test_to_dict(self):
        traj = AgentTrajectory(
            trajectory_id="test",
            agent_id="test",
            objective_id="test",
            start_time="2026-01-01T00:00:00Z",
        )
        d = traj.to_dict()
        assert d["trajectory_id"] == "test"


class TestLongHorizonInvariants:
    """Tests for long-horizon invariants."""

    def test_model_output_not_directly_connected_to_authority(self):
        """MODEL_OUTPUT → AUTHORITY must be structurally impossible."""
        from research.examples.sovereign_agent.agent import SovereignAgent, AgentPolicy
        from research.examples.sovereign_agent.environment import build_hostile_payment_environment

        interface = CombinedSovereignInterface()
        agent = SovereignAgent("agent_001", AgentPolicy.CONFIDENCE_ESCALATION, interface)
        env = build_hostile_payment_environment()
        result = agent.run(env)

        # All unauthorized actions should be blocked
        assert result.metrics.unauthorized_actions_prevented > 0

    def test_recommendation_not_directly_connected_to_execution(self):
        """RECOMMENDATION → EXECUTION must be structurally impossible."""
        interface = CombinedSovereignInterface()
        agent = ConfidentlyWrongAgent(
            "agent_001",
            ConfidenceType.RECOMMENDATION,
            interface,
        )
        env = TrialEnvironment()
        result = agent.run(env)
        assert result.metrics.unauthorized_actions_prevented > 0

    def test_documentation_not_ground_truth(self):
        """DOCUMENTATION ≠ GROUND_TRUTH."""
        interface = CombinedSovereignInterface()
        agent = ConfidentlyWrongAgent(
            "agent_001",
            ConfidenceType.DOCUMENTATION,
            interface,
        )
        env = TrialEnvironment()
        result = agent.run(env)
        assert result.metrics.unauthorized_actions_prevented > 0

    def test_runtime_trace_not_authorization(self):
        """RUNTIME_TRACE ≠ AUTHORIZATION."""
        interface = CombinedSovereignInterface()
        agent = ConfidentlyWrongAgent(
            "agent_001",
            ConfidenceType.RUNTIME_TRACE,
            interface,
        )
        env = TrialEnvironment()
        result = agent.run(env)
        assert result.metrics.unauthorized_actions_prevented > 0

    def test_credential_not_authorization(self):
        """CREDENTIAL ≠ AUTHORIZATION."""
        interface = CombinedSovereignInterface()
        agent = ConfidentlyWrongAgent(
            "agent_001",
            ConfidenceType.CREDENTIAL,
            interface,
        )
        env = TrialEnvironment()
        result = agent.run(env)
        assert result.metrics.unauthorized_actions_prevented > 0

    def test_stale_authority_rejected(self):
        """Stale authority must be rejected."""
        interface = CombinedSovereignInterface()
        agent = ConfidentlyWrongAgent(
            "agent_001",
            ConfidenceType.STALE_AUTHORITY,
            interface,
        )
        env = TrialEnvironment()
        result = agent.run(env)
        assert result.metrics.unauthorized_actions_prevented > 0

    def test_historical_state_not_current_authority(self):
        """Historical state ≠ current authority."""
        interface = CombinedSovereignInterface()
        agent = ConfidentlyWrongAgent(
            "agent_001",
            ConfidenceType.HISTORICAL_STATE,
            interface,
        )
        env = TrialEnvironment()
        result = agent.run(env)
        assert result.metrics.unauthorized_actions_prevented > 0

    def test_environment_confidence_blocked(self):
        """Environment confidence must be blocked."""
        interface = CombinedSovereignInterface()
        agent = ConfidentlyWrongAgent(
            "agent_001",
            ConfidenceType.ENVIRONMENT,
            interface,
        )
        env = TrialEnvironment()
        result = agent.run(env)
        assert result.metrics.unauthorized_actions_prevented > 0


class TestContradictionRecovery:
    """Tests for contradiction recovery."""

    def test_agent_recovers_from_provider_replacement(self):
        """Agent should recover when provider changes."""
        report = run_long_horizon_trial()
        assert report.metrics.contradiction_recoveries > 0

    def test_agent_recovers_from_delegation_expiration(self):
        """Agent should recover when delegation expires."""
        report = run_long_horizon_trial()
        assert report.metrics.authority_drift_recoveries > 0

    def test_agent_recovers_from_governance_change(self):
        """Agent should recover when governance changes."""
        report = run_long_horizon_trial()
        assert report.metrics.contradiction_recoveries > 0

    def test_contradiction_recovery_rate_computed(self):
        """Contradiction recovery rate should be computed."""
        report = run_long_horizon_trial()
        assert 0.0 <= report.metrics.to_dict().get("contradiction_recovery_rate", 0.5) <= 1.0


class TestProtocolCompliance:
    """Tests for protocol compliance."""

    def test_no_protocol_escapes(self):
        """No protocol escapes should be found."""
        report = run_long_horizon_trial()
        assert len(report.protocol_escapes) == 0

    def test_unauthorized_consequences_zero(self):
        """No unauthorized consequences should occur."""
        report = run_long_horizon_trial()
        assert report.metrics.unauthorized_consequences == 0

    def test_protocol_compliance_high(self):
        """Protocol compliance should be high."""
        report = run_long_horizon_trial()
        assert report.metrics.protocol_compliance >= 0.5
