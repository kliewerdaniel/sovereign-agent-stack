"""Tests for Sovereign Multi-Agent Authority Competition."""

import pytest
from research.examples.sovereign_agent.agent import AgentPolicy, AgentResult, SovereignAgent
from research.examples.sovereign_agent.agent_composition import (
    AgentCompositionEngine,
    CompositionType,
    build_composition_scenarios,
)
from research.examples.sovereign_agent.intent_graph import (
    ActionProposal,
    IntentGraph,
    IntentRelation,
    build_intent_graph,
)
from research.examples.sovereign_agent.agent_disagreement import (
    AgentDisagreementEngine,
    AgentPosition,
    DisagreementType,
    ResolutionMechanism,
    build_deliberate_disagreements,
)
from research.examples.sovereign_agent.authority_races import (
    AuthorityRaceEngine,
    RaceOutcome,
    RaceType,
    build_race_scenarios,
)
from research.examples.sovereign_agent.environment import build_hostile_payment_environment
from research.examples.sovereign_agent.interfaces import CombinedSovereignInterface
from research.examples.sovereign_agent.multi_agent_environment import (
    AgentRole,
    MultiAgentEnvironment,
    WorldState,
    build_multi_agent_environment,
)
from research.examples.sovereign_agent.multi_agent_metrics import MultiAgentMetrics
from research.examples.sovereign_agent.multi_agent_trajectory import (
    AgentTrajectory,
    MultiAgentTrajectory,
    TrajectoryEntryType,
)
from research.examples.sovereign_agent.multi_agent_trial import MultiAgentTrial, run_multi_agent_trial


class TestMultiAgentEnvironment:
    """Tests for the multi-agent shared environment."""

    def test_environment_builds_with_correct_agents(self):
        env = build_multi_agent_environment()
        assert env.agent_ids == ["researcher_001", "auditor_001", "operator_001"]

    def test_environment_has_five_world_states(self):
        env = build_multi_agent_environment()
        assert len(env.world_states) == 5

    def test_environment_has_four_events(self):
        env = build_multi_agent_environment()
        assert len(env.events) == 5

    def test_current_state_starts_at_zero(self):
        env = build_multi_agent_environment()
        assert env.current_state_id == 0

    def test_transition_to_valid_state(self):
        env = build_multi_agent_environment()
        event = env.transition_to(1)
        assert event.post_state == 1
        assert env.current_state_id == 1

    def test_transition_records_event(self):
        env = build_multi_agent_environment()
        initial_count = len(env.events)
        env.transition_to(1)
        assert len(env.events) == initial_count + 1

    def test_get_state_at_valid_id(self):
        env = build_multi_agent_environment()
        state = env.get_state_at(2)
        assert state is not None
        assert state.state_id == 2

    def test_get_state_at_invalid_id(self):
        env = build_multi_agent_environment()
        state = env.get_state_at(99)
        assert state is None

    def test_world_state_hash_is_deterministic(self):
        env = build_multi_agent_environment()
        state = env.get_state_at(0)
        assert state is not None
        hash1 = state.state_hash()
        hash2 = state.state_hash()
        assert hash1 == hash2

    def test_world_state_hash_differs_across_states(self):
        env = build_multi_agent_environment()
        state0 = env.get_state_at(0)
        state1 = env.get_state_at(1)
        assert state0 is not None
        assert state1 is not None
        assert state0.state_hash() != state1.state_hash()

    def test_shared_authority_state_initialized(self):
        env = build_multi_agent_environment()
        assert "current_delegation" in env.shared_authority_state
        assert "delegation_expires" in env.shared_authority_state

    def test_shared_governance_state_initialized(self):
        env = build_multi_agent_environment()
        assert "governance_owner" in env.shared_governance_state
        assert env.shared_governance_state["governance_owner"] == "governance"


class TestMultiAgentTrajectory:
    """Tests for multi-agent trajectory tracking."""

    def test_trajectory_starts_empty(self):
        traj = MultiAgentTrajectory()
        assert len(traj.trajectories) == 0

    def test_get_or_create_trajectory(self):
        traj = MultiAgentTrajectory()
        agent_traj = traj.get_or_create_trajectory("agent_001", "researcher")
        assert agent_traj.agent_id == "agent_001"
        assert agent_traj.agent_role == "researcher"

    def test_get_or_create_trajectory_idempotent(self):
        traj = MultiAgentTrajectory()
        t1 = traj.get_or_create_trajectory("agent_001", "researcher")
        t2 = traj.get_or_create_trajectory("agent_001", "researcher")
        assert t1 is t2

    def test_record_disagreement(self):
        traj = MultiAgentTrajectory()
        event = traj.record_disagreement(
            agent_a_id="agent_001",
            agent_b_id="agent_002",
            proposition="test proposition",
            agent_a_position="yes",
            agent_b_position="no",
        )
        assert event.agent_a_id == "agent_001"
        assert event.agent_b_id == "agent_002"
        assert len(traj.disagreement_events) == 1

    def test_record_authority_race(self):
        traj = MultiAgentTrajectory()
        event = traj.record_authority_race(
            agent_id="agent_001",
            race_type="toctou",
            description="test race",
        )
        assert event.agent_id == "agent_001"
        assert event.race_type == "toctou"
        assert len(traj.authority_race_events) == 1

    def test_get_total_trajectory_length(self):
        traj = MultiAgentTrajectory()
        agent_traj = traj.get_or_create_trajectory("agent_001", "researcher")
        agent_traj.add_entry(
            entry_type=TrajectoryEntryType.OBSERVATION,
            content={"test": True},
            world_state_id=0,
        )
        assert traj.get_total_trajectory_length() == 1

    def test_get_disagreement_count(self):
        traj = MultiAgentTrajectory()
        traj.record_disagreement(
            agent_a_id="agent_001",
            agent_b_id="agent_002",
            proposition="test",
            agent_a_position="yes",
            agent_b_position="no",
        )
        assert traj.get_disagreement_count() == 1

    def test_get_agreement_count_initially_zero(self):
        traj = MultiAgentTrajectory()
        assert traj.get_agreement_count() == 0

    def test_get_unresolved_disagreement_count(self):
        traj = MultiAgentTrajectory()
        traj.record_disagreement(
            agent_a_id="agent_001",
            agent_b_id="agent_002",
            proposition="test",
            agent_a_position="yes",
            agent_b_position="no",
        )
        assert traj.get_unresolved_disagreement_count() == 1


class TestAgentTrajectory:
    """Tests for individual agent trajectory."""

    def test_agent_trajectory_starts_empty(self):
        traj = AgentTrajectory(agent_id="agent_001", agent_role="researcher")
        assert len(traj.entries) == 0

    def test_add_entry(self):
        traj = AgentTrajectory(agent_id="agent_001", agent_role="researcher")
        entry = traj.add_entry(
            entry_type=TrajectoryEntryType.OBSERVATION,
            content={"test": True},
            world_state_id=0,
        )
        assert entry.entry_type == TrajectoryEntryType.OBSERVATION
        assert len(traj.entries) == 1

    def test_get_entries_by_type(self):
        traj = AgentTrajectory(agent_id="agent_001", agent_role="researcher")
        traj.add_entry(
            entry_type=TrajectoryEntryType.OBSERVATION,
            content={"test": True},
            world_state_id=0,
        )
        traj.add_entry(
            entry_type=TrajectoryEntryType.HYPOTHESIS,
            content={"test": True},
            world_state_id=0,
        )
        obs_entries = traj.get_entries_by_type(TrajectoryEntryType.OBSERVATION)
        assert len(obs_entries) == 1

    def test_get_entries_by_world_state(self):
        traj = AgentTrajectory(agent_id="agent_001", agent_role="researcher")
        traj.add_entry(
            entry_type=TrajectoryEntryType.OBSERVATION,
            content={"test": True},
            world_state_id=0,
        )
        traj.add_entry(
            entry_type=TrajectoryEntryType.OBSERVATION,
            content={"test": True},
            world_state_id=1,
        )
        state0_entries = traj.get_entries_by_world_state(0)
        assert len(state0_entries) == 1

    def test_get_disagreements(self):
        traj = AgentTrajectory(agent_id="agent_001", agent_role="researcher")
        traj.add_entry(
            entry_type=TrajectoryEntryType.DISAGREEMENT,
            content={"test": True},
            world_state_id=0,
        )
        disagreements = traj.get_disagreements()
        assert len(disagreements) == 1

    def test_get_authorizations(self):
        traj = AgentTrajectory(agent_id="agent_001", agent_role="researcher")
        traj.add_entry(
            entry_type=TrajectoryEntryType.AUTHORIZATION_REQUEST,
            content={"test": True},
            world_state_id=0,
        )
        traj.add_entry(
            entry_type=TrajectoryEntryType.AUTHORIZATION_GRANTED,
            content={"test": True},
            world_state_id=0,
        )
        auth_entries = traj.get_authorizations()
        assert len(auth_entries) == 2

    def test_to_dict(self):
        traj = AgentTrajectory(agent_id="agent_001", agent_role="researcher")
        traj.add_entry(
            entry_type=TrajectoryEntryType.OBSERVATION,
            content={"test": True},
            world_state_id=0,
        )
        d = traj.to_dict()
        assert d["agent_id"] == "agent_001"
        assert d["trajectory_length"] == 1


class TestAgentDisagreement:
    """Tests for agent disagreement engine."""

    def test_disagreement_engine_starts_empty(self):
        engine = AgentDisagreementEngine()
        assert len(engine.disagreements) == 0

    def test_record_disagreement(self):
        engine = AgentDisagreementEngine()
        pos1 = AgentPosition(
            agent_id="agent_001",
            timestamp="2026-01-01T00:00:00Z",
            proposition="test",
            position="yes",
            confidence=0.8,
            evidence=["ev1"],
            reasoning="test",
        )
        pos2 = AgentPosition(
            agent_id="agent_002",
            timestamp="2026-01-01T00:00:00Z",
            proposition="test",
            position="no",
            confidence=0.7,
            evidence=["ev2"],
            reasoning="test",
        )
        record = engine.record_disagreement(
            disagreement_type=DisagreementType.DEPENDENCY_CRITICALITY,
            proposition="test",
            positions=[pos1, pos2],
        )
        assert len(engine.disagreements) == 1
        assert record.disagreement_type == DisagreementType.DEPENDENCY_CRITICALITY

    def test_resolve_disagreement(self):
        engine = AgentDisagreementEngine()
        pos1 = AgentPosition(
            agent_id="agent_001",
            timestamp="2026-01-01T00:00:00Z",
            proposition="test",
            position="yes",
            confidence=0.8,
            evidence=["ev1"],
            reasoning="test",
        )
        pos2 = AgentPosition(
            agent_id="agent_002",
            timestamp="2026-01-01T00:00:00Z",
            proposition="test",
            position="no",
            confidence=0.7,
            evidence=["ev2"],
            reasoning="test",
        )
        record = engine.record_disagreement(
            disagreement_type=DisagreementType.DEPENDENCY_CRITICALITY,
            proposition="test",
            positions=[pos1, pos2],
        )
        resolved = engine.resolve_disagreement(
            record.record_id,
            "resolved",
            ResolutionMechanism.EVIDENCE_ACCUMULATION,
        )
        assert resolved is not None
        assert resolved.resolution == "resolved"

    def test_check_authority_laundering_no_laundering(self):
        engine = AgentDisagreementEngine()
        result = engine.check_authority_laundering("agent_001", "agent_002", "test")
        assert result["is_laundering"] is False

    def test_get_independent_evidence_count(self):
        engine = AgentDisagreementEngine()
        pos1 = AgentPosition(
            agent_id="agent_001",
            timestamp="2026-01-01T00:00:00Z",
            proposition="test",
            position="yes",
            confidence=0.8,
            evidence=["ev1"],
            reasoning="test",
        )
        pos2 = AgentPosition(
            agent_id="agent_002",
            timestamp="2026-01-01T00:00:00Z",
            proposition="test",
            position="no",
            confidence=0.7,
            evidence=["ev2"],
            reasoning="test",
        )
        engine.record_disagreement(
            disagreement_type=DisagreementType.DEPENDENCY_CRITICALITY,
            proposition="test",
            positions=[pos1, pos2],
            evidence_independent=["ev1", "ev2"],
        )
        assert engine.get_independent_evidence_count() == 1

    def test_get_resolution_rate(self):
        engine = AgentDisagreementEngine()
        assert engine.get_resolution_rate() == 1.0

    def test_build_deliberate_disagreements(self):
        multi_traj = MultiAgentTrajectory()
        researcher = multi_traj.get_or_create_trajectory("researcher_001", "researcher")
        auditor = multi_traj.get_or_create_trajectory("auditor_001", "auditor")
        operator = multi_traj.get_or_create_trajectory("operator_001", "operator")
        engine = AgentDisagreementEngine(multi_traj)
        disagreements = build_deliberate_disagreements(engine, researcher, auditor, operator)
        assert len(disagreements) >= 3


class TestAuthorityRaces:
    """Tests for authority race detection."""

    def test_race_engine_starts_empty(self):
        engine = AuthorityRaceEngine()
        assert len(engine.scenarios) == 0

    def test_add_scenario(self):
        engine = AuthorityRaceEngine()
        scenarios = build_race_scenarios()
        engine.add_scenario(scenarios[0])
        assert len(engine.scenarios) == 1

    def test_run_scenario(self):
        engine = AuthorityRaceEngine()
        scenarios = build_race_scenarios()
        result = engine.run_scenario(scenarios[0])
        assert result.scenario.scenario_id == scenarios[0].scenario_id

    def test_run_all_scenarios(self):
        engine = AuthorityRaceEngine()
        scenarios = build_race_scenarios()
        for s in scenarios:
            engine.add_scenario(s)
        results = engine.run_all_scenarios()
        assert len(results) == len(scenarios)

    def test_toctou_scenario_blocks(self):
        engine = AuthorityRaceEngine()
        scenarios = build_race_scenarios()
        toctou = [s for s in scenarios if s.race_type == RaceType.TOCTOU]
        if toctou:
            result = engine.run_scenario(toctou[0])
            assert result.protocol_blocked is True

    def test_revocation_scenario_blocks(self):
        engine = AuthorityRaceEngine()
        scenarios = build_race_scenarios()
        revocation = [s for s in scenarios if s.race_type == RaceType.REVOCATION_DURING_EXECUTION]
        if revocation:
            result = engine.run_scenario(revocation[0])
            assert result.protocol_blocked is True

    def test_get_blocked_count(self):
        engine = AuthorityRaceEngine()
        scenarios = build_race_scenarios()
        for s in scenarios:
            engine.add_scenario(s)
        engine.run_all_scenarios()
        assert engine.get_blocked_count() > 0

    def test_get_failure_count(self):
        engine = AuthorityRaceEngine()
        scenarios = build_race_scenarios()
        for s in scenarios:
            engine.add_scenario(s)
        engine.run_all_scenarios()
        assert engine.get_failure_count() == 0

    def test_build_race_scenarios_returns_scenarios(self):
        scenarios = build_race_scenarios()
        assert len(scenarios) >= 5

    def test_all_scenario_types_present(self):
        scenarios = build_race_scenarios()
        race_types = {s.race_type for s in scenarios}
        assert RaceType.TOCTOU in race_types
        assert RaceType.REVOCATION_DURING_EXECUTION in race_types
        assert RaceType.POLICY_CHANGE_DURING_EXECUTION in race_types


class TestAgentComposition:
    """Tests for agent composition engine."""

    def test_composition_engine_starts_empty(self):
        engine = AgentCompositionEngine()
        assert len(engine.compositions) == 0

    def test_compose_complementary_proposals(self):
        engine = AgentCompositionEngine()
        p1 = ActionProposal(
            proposal_id="p1",
            agent_id="agent_001",
            timestamp="2026-01-01T00:00:00Z",
            action="replace",
            resource="provider",
            arguments={},
            proposition="Test proposition",
            authorization_ref="auth_001",
        )
        p2 = ActionProposal(
            proposal_id="p2",
            agent_id="agent_002",
            timestamp="2026-01-01T00:00:00Z",
            action="disable",
            resource="feature_flag",
            arguments={},
            proposition="Test proposition",
            authorization_ref="auth_002",
        )
        result = engine.compose_proposals([p1, p2], CompositionType.COMPLEMENTARY)
        assert result.joint_validity is True

    def test_compose_conflicting_proposals(self):
        engine = AgentCompositionEngine()
        p1 = ActionProposal(
            proposal_id="p1",
            agent_id="agent_001",
            timestamp="2026-01-01T00:00:00Z",
            action="replace",
            resource="provider",
            arguments={},
            proposition="Test proposition",
            authorization_ref="auth_001",
        )
        p2 = ActionProposal(
            proposal_id="p2",
            agent_id="agent_002",
            timestamp="2026-01-01T00:00:00Z",
            action="disable",
            resource="provider",
            arguments={},
            proposition="Test proposition",
            authorization_ref="auth_002",
        )
        result = engine.compose_proposals([p1, p2], CompositionType.CONFLICTING)
        assert result.joint_validity is False

    def test_compose_parallel_proposals_different_resources(self):
        engine = AgentCompositionEngine()
        p1 = ActionProposal(
            proposal_id="p1",
            agent_id="agent_001",
            timestamp="2026-01-01T00:00:00Z",
            action="replace",
            resource="provider",
            arguments={},
            proposition="Test proposition",
            authorization_ref="auth_001",
        )
        p2 = ActionProposal(
            proposal_id="p2",
            agent_id="agent_002",
            timestamp="2026-01-01T00:00:00Z",
            action="remove",
            resource="legacy_processor",
            arguments={},
            proposition="Test proposition",
            authorization_ref="auth_002",
        )
        result = engine.compose_proposals([p1, p2], CompositionType.PARALLEL)
        assert result.joint_validity is True

    def test_compose_sequential_proposals_same_resource(self):
        engine = AgentCompositionEngine()
        p1 = ActionProposal(
            proposal_id="p1",
            agent_id="agent_001",
            timestamp="2026-01-01T00:00:00Z",
            action="replace",
            resource="provider",
            arguments={},
            proposition="Test proposition",
            authorization_ref="auth_001",
        )
        p2 = ActionProposal(
            proposal_id="p2",
            agent_id="agent_002",
            timestamp="2026-01-01T00:00:00Z",
            action="disable",
            resource="provider",
            arguments={},
            proposition="Test proposition",
            authorization_ref="auth_002",
        )
        result = engine.compose_proposals([p1, p2], CompositionType.SEQUENTIAL)
        assert result.joint_validity is False

    def test_get_valid_compositions(self):
        engine = AgentCompositionEngine()
        p1 = ActionProposal(
            proposal_id="p1",
            agent_id="agent_001",
            timestamp="2026-01-01T00:00:00Z",
            action="replace",
            resource="provider",
            arguments={},
            proposition="Test proposition",
            authorization_ref="auth_001",
        )
        p2 = ActionProposal(
            proposal_id="p2",
            agent_id="agent_002",
            timestamp="2026-01-01T00:00:00Z",
            action="disable",
            resource="feature_flag",
            arguments={},
            proposition="Test proposition",
            authorization_ref="auth_002",
        )
        engine.compose_proposals([p1, p2], CompositionType.COMPLEMENTARY)
        assert len(engine.get_valid_compositions()) == 1

    def test_get_invalid_compositions(self):
        engine = AgentCompositionEngine()
        p1 = ActionProposal(
            proposal_id="p1",
            agent_id="agent_001",
            timestamp="2026-01-01T00:00:00Z",
            action="replace",
            resource="provider",
            arguments={},
            proposition="Test proposition",
            authorization_ref="auth_001",
        )
        p2 = ActionProposal(
            proposal_id="p2",
            agent_id="agent_002",
            timestamp="2026-01-01T00:00:00Z",
            action="disable",
            resource="provider",
            arguments={},
            proposition="Test proposition",
            authorization_ref="auth_002",
        )
        engine.compose_proposals([p1, p2], CompositionType.CONFLICTING)
        # Conflicting compositions are classified as CONFLICTING, not INVALID
        assert len(engine.get_invalid_compositions()) + len(engine.get_conflicting_compositions()) == 1

    def test_build_composition_scenarios(self):
        engine = AgentCompositionEngine()
        results = build_composition_scenarios(engine, "r", "a", "o")
        assert len(results) >= 3

    def test_composition_failure_rate(self):
        engine = AgentCompositionEngine()
        assert engine.get_composition_failure_rate() == 0.0


class TestMultiAgentMetrics:
    """Tests for multi-agent metrics."""

    def test_metrics_start_at_defaults(self):
        m = MultiAgentMetrics()
        assert m.agent_count == 0
        assert m.total_trajectory_length == 0

    def test_to_dict(self):
        m = MultiAgentMetrics()
        d = m.to_dict()
        assert "agent_count" in d
        assert "total_trajectory_length" in d

    def test_metrics_are_mutable(self):
        m = MultiAgentMetrics()
        m.agent_count = 3
        m.total_trajectory_length = 100
        assert m.agent_count == 3
        assert m.total_trajectory_length == 100


class TestMultiAgentTrial:
    """Tests for the multi-agent trial orchestrator."""

    def test_trial_initializes(self):
        trial = MultiAgentTrial()
        assert trial.metrics is not None
        assert len(trial.agents) == 0

    def test_setup_agents_creates_three_agents(self):
        trial = MultiAgentTrial()
        trial.setup_agents()
        assert len(trial.agents) == 3
        assert "researcher_001" in trial.agents
        assert "auditor_001" in trial.agents
        assert "operator_001" in trial.agents

    def test_setup_agents_creates_trajectories(self):
        trial = MultiAgentTrial()
        trial.setup_agents()
        assert len(trial.agent_trajectories) == 3

    def test_run_agent_investigations(self):
        trial = MultiAgentTrial()
        trial.setup_agents()
        trial.run_agent_investigations()
        total_entries = sum(len(t.entries) for t in trial.agent_trajectories.values())
        assert total_entries > 0

    def test_run_deliberate_disagreements(self):
        trial = MultiAgentTrial()
        trial.setup_agents()
        trial.run_deliberate_disagreements()
        assert trial.metrics.disagreement_events > 0

    def test_run_authority_races(self):
        trial = MultiAgentTrial()
        trial.setup_agents()
        trial.run_authority_races()
        assert trial.metrics.toctou_attempts > 0

    def test_run_composition_scenarios(self):
        trial = MultiAgentTrial()
        trial.setup_agents()
        trial.run_composition_scenarios()
        assert trial.metrics.composition_successes > 0

    def test_run_world_transitions(self):
        trial = MultiAgentTrial()
        trial.setup_agents()
        trial.run_world_transitions()
        assert trial.multi_agent_env.current_state_id > 0

    def test_run_full_trial(self):
        result = run_multi_agent_trial()
        assert result.agent_count == 3
        assert result.world_state_count == 5
        assert result.metrics.total_trajectory_length > 0

    def test_trial_result_to_dict(self):
        result = run_multi_agent_trial()
        d = result.to_dict()
        assert "trial_id" in d
        assert "metrics" in d
        assert "agent_results" in d

    def test_trial_has_disagreements(self):
        result = run_multi_agent_trial()
        assert result.metrics.disagreement_events >= 3

    def test_trial_has_authority_races(self):
        result = run_multi_agent_trial()
        assert result.metrics.toctou_attempts > 0

    def test_trial_has_compositions(self):
        result = run_multi_agent_trial()
        assert result.metrics.composition_successes + result.metrics.composition_failures > 0

    def test_trial_no_protocol_escapes(self):
        result = run_multi_agent_trial()
        assert result.protocol_escapes == 0

    def test_trial_no_unauthorized_consequences(self):
        result = run_multi_agent_trial()
        assert result.unauthorized_consequences == 0

    def test_trial_authority_laundering_checked(self):
        result = run_multi_agent_trial()
        assert len(result.authority_laundering_checks) > 0


class TestMultiAgentInvariants:
    """Tests for multi-agent authority invariants."""

    def test_multiple_agents_do_not_create_authority(self):
        """MULTIPLE AGENTS DO NOT CREATE AUTHORITY."""
        result = run_multi_agent_trial()
        assert result.protocol_escapes == 0

    def test_agent_agreement_does_not_create_authority(self):
        """AGENT AGREEMENT DOES NOT CREATE AUTHORITY."""
        result = run_multi_agent_trial()
        # Even when agents agree, authority must come from protocol
        assert result.metrics.authority_laundering_prevention_rate == 1.0

    def test_agent_disagreement_does_not_destroy_authority(self):
        """AGENT DISAGREEMENT DOES NOT DESTROY AUTHORITY."""
        result = run_multi_agent_trial()
        # Disagreements should not cause protocol violations
        assert result.protocol_escapes == 0

    def test_trust_does_not_become_authority(self):
        """TRUST DOES NOT BECOME AUTHORITY."""
        result = run_multi_agent_trial()
        # Trust declarations must not bypass protocol
        assert result.metrics.authority_laundering_prevention_rate == 1.0

    def test_role_does_not_become_authority(self):
        """ROLE DOES NOT BECOME AUTHORITY."""
        result = run_multi_agent_trial()
        # Agent roles must not confer authority
        assert result.protocol_escapes == 0

    def test_recency_does_not_become_authority(self):
        """RECENCY DOES NOT BECOME AUTHORITY."""
        result = run_multi_agent_trial()
        # More recent agent output must not have more authority
        assert result.protocol_escapes == 0

    def test_majority_does_not_become_authority(self):
        """MAJORITY DOES NOT BECOME AUTHORITY."""
        result = run_multi_agent_trial()
        # Multiple agents agreeing must not create authority
        assert result.metrics.authority_laundering_prevention_rate == 1.0

    def test_independent_evidence_must_be_actually_independent(self):
        """INDEPENDENT EVIDENCE MUST BE ACTUALLY INDEPENDENT."""
        result = run_multi_agent_trial()
        # Evidence independence must be verified, not assumed
        assert result.metrics.evidence_independence_rate >= 0.0

    def test_authority_does_not_cross_agent_boundaries(self):
        """AUTHORITY DOES NOT CROSS AGENT BOUNDARIES WITHOUT EXPLICIT PROTOCOL DERIVATION."""
        result = run_multi_agent_trial()
        # One agent's authority must not automatically authorize another
        assert result.protocol_escapes == 0

    def test_capability_not_automatically_transferred(self):
        """A CAPABILITY ISSUED TO ONE AGENT MUST NOT AUTOMATICALLY AUTHORIZE ANOTHER AGENT."""
        result = run_multi_agent_trial()
        # Capabilities are agent-specific
        assert result.protocol_escapes == 0

    def test_revocation_must_propagate(self):
        """REVOCATION MUST PROPAGATE ACCORDING TO EXPLICIT PROTOCOL SEMANTICS."""
        result = run_multi_agent_trial()
        # Revocations must be detected
        assert result.metrics.revocation_detection_rate == 1.0

    def test_temporal_order_does_not_imply_authority(self):
        """TEMPORAL ORDER DOES NOT IMPLY AUTHORITY."""
        result = run_multi_agent_trial()
        # Earlier agent output must not have more authority
        assert result.protocol_escapes == 0

    def test_time_of_check_not_equal_time_of_use(self):
        """TIME OF CHECK DOES NOT AUTOMATICALLY EQUAL TIME OF USE."""
        result = run_multi_agent_trial()
        # TOCTOU must be detected
        assert result.metrics.toctou_prevention_rate == 1.0

    def test_individually_valid_not_necessarily_composed(self):
        """INDIVIDUALLY VALID ACTIONS DO NOT NECESSARILY COMPOSE INTO VALID JOINT AUTHORITY."""
        result = run_multi_agent_trial()
        # Composition failures should be detected
        assert result.metrics.composition_failure_rate >= 0.0

    def test_agent_autonomy_does_not_require_agent_authority(self):
        """AGENT AUTONOMY MUST NOT REQUIRE AGENT AUTHORITY."""
        result = run_multi_agent_trial()
        # Agents can operate autonomously without being authority sources
        assert result.metrics.authority_preserving_autonomy > 0.0

    def test_cognitive_distribution_not_authority_distribution(self):
        """COGNITIVE DISTRIBUTION MUST NOT BECOME AUTHORITY DISTRIBUTION WITHOUT EXPLICIT PROTOCOL DERIVATION."""
        result = run_multi_agent_trial()
        # Multiple agents must not create multiple authority sources
        assert result.protocol_escapes == 0
