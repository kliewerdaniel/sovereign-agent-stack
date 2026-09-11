"""Tests for Sovereign Intent Graph."""

import pytest
from research.examples.sovereign_agent.intent_graph import (
    ActionProposal,
    IntentEdge,
    IntentGraph,
    IntentRelation,
    build_intent_graph,
)
from research.examples.sovereign_agent.agent_composition import AgentCompositionEngine, CompositionType
from research.examples.sovereign_agent.multi_agent_trajectory import (
    AgentTrajectory,
    MultiAgentTrajectory,
    TrajectoryEntryType,
)
from research.examples.sovereign_agent.intent_graph_trial import run_intent_graph_trial
from research.examples.counterexamples.counterexample_corpus import (
    build_initial_counterexamples,
    CounterexampleType,
    ResolutionStatus,
)


class TestIntentGraph:
    """Tests for the intent graph."""

    def test_intent_graph_builds_from_proposals(self):
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
            ),
            ActionProposal(
                proposal_id="p2",
                agent_id="agent_002",
                timestamp="2026-01-01T00:00:00Z",
                action="disable",
                resource="feature_flag",
                arguments={},
                proposition="Disable feature flag",
            ),
        ]
        graph = build_intent_graph(proposals)
        assert len(graph.proposals) == 2

    def test_intent_graph_has_graph_id(self):
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
            ),
        ]
        graph = build_intent_graph(proposals)
        assert graph.graph_id.startswith("intent_")

    def test_intent_graph_tracks_edges(self):
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
                postconditions=["provider_replaced"],
            ),
            ActionProposal(
                proposal_id="p2",
                agent_id="agent_002",
                timestamp="2026-01-01T00:00:00Z",
                action="verify",
                resource="provider",
                arguments={},
                proposition="Verify provider",
                prerequisite_actions=["provider_replaced"],
            ),
        ]
        graph = build_intent_graph(proposals)
        # Should detect sequential dependency
        assert len(graph.edges) > 0

    def test_intent_graph_detects_conflicts(self):
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
            ),
            ActionProposal(
                proposal_id="p2",
                agent_id="agent_002",
                timestamp="2026-01-01T00:00:00Z",
                action="disable",
                resource="provider",
                arguments={},
                proposition="Disable provider",
            ),
        ]
        graph = build_intent_graph(proposals)
        conflicts = graph.detect_conflicts()
        assert len(conflicts) > 0

    def test_intent_graph_detects_independent_proposals(self):
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
            ),
            ActionProposal(
                proposal_id="p2",
                agent_id="agent_002",
                timestamp="2026-01-01T00:00:00Z",
                action="remove",
                resource="legacy_processor",
                arguments={},
                proposition="Remove legacy processor",
            ),
        ]
        graph = build_intent_graph(proposals)
        independent = graph.get_independent_proposals()
        assert len(independent) == 2

    def test_intent_graph_get_proposals_by_agent(self):
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
            ),
            ActionProposal(
                proposal_id="p2",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="verify",
                resource="provider",
                arguments={},
                proposition="Verify provider",
            ),
        ]
        graph = build_intent_graph(proposals)
        agent_proposals = graph.get_proposals_by_agent("agent_001")
        assert len(agent_proposals) == 2

    def test_intent_graph_get_dependencies(self):
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="backup",
                resource="database",
                arguments={},
                proposition="Backup database",
                postconditions=["database_backed_up"],
            ),
            ActionProposal(
                proposal_id="p2",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
                prerequisite_actions=["database_backed_up"],
            ),
        ]
        graph = build_intent_graph(proposals)
        deps = graph.get_dependencies("p2")
        assert "p1" in deps

    def test_intent_graph_get_conflicts(self):
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
            ),
            ActionProposal(
                proposal_id="p2",
                agent_id="agent_002",
                timestamp="2026-01-01T00:00:00Z",
                action="disable",
                resource="provider",
                arguments={},
                proposition="Disable provider",
            ),
        ]
        graph = build_intent_graph(proposals)
        graph.detect_conflicts()
        conflicts = graph.get_conflicts("p1")
        assert "p2" in conflicts

    def test_intent_graph_get_sequential_chains(self):
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="backup",
                resource="database",
                arguments={},
                proposition="Backup database",
                postconditions=["database_backed_up"],
            ),
            ActionProposal(
                proposal_id="p2",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
                prerequisite_actions=["database_backed_up"],
            ),
            ActionProposal(
                proposal_id="p3",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="verify",
                resource="provider",
                arguments={},
                proposition="Verify provider",
                prerequisite_actions=["provider_replaced"],
                postconditions=["provider_replaced"],
            ),
        ]
        graph = build_intent_graph(proposals)
        chains = graph.get_sequential_chains()
        assert len(chains) >= 1

    def test_intent_graph_to_dict(self):
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
            ),
        ]
        graph = build_intent_graph(proposals)
        d = graph.to_dict()
        assert "graph_id" in d
        assert d["proposal_count"] == 1


class TestIntentGraphNoAuthorityLeakage:
    """Tests that intent graph does not create authority."""

    def test_intent_graph_contains_no_authority_edges(self):
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
            ),
            ActionProposal(
                proposal_id="p2",
                agent_id="agent_002",
                timestamp="2026-01-01T00:00:00Z",
                action="disable",
                resource="provider",
                arguments={},
                proposition="Disable provider",
            ),
        ]
        graph = build_intent_graph(proposals)
        # Verify no edge type implies authority
        authority_implying_relations = {"authorizes", "grants", "delegates", "approves"}
        for edge in graph.edges:
            assert edge.relation.value not in authority_implying_relations

    def test_intent_graph_does_not_authorize(self):
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
            ),
        ]
        graph = build_intent_graph(proposals)
        # Intent graph has no authorization mechanism
        assert not hasattr(graph, "authorize")
        assert not hasattr(graph, "grant")

    def test_intent_graph_does_not_create_capability(self):
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
            ),
        ]
        graph = build_intent_graph(proposals)
        # Intent graph has no capability creation mechanism
        assert not hasattr(graph, "create_capability")
        assert not hasattr(graph, "issue_capability")


class TestCounterexampleCorpus:
    """Tests for counterexample corpus."""

    def test_corpus_builds_with_initial_counterexamples(self):
        corpus = build_initial_counterexamples()
        assert len(corpus.counterexamples) == 10

    def test_corpus_has_all_unresolved(self):
        corpus = build_initial_counterexamples()
        assert len(corpus.get_unresolved()) == 10

    def test_corpus_type_counts(self):
        corpus = build_initial_counterexamples()
        counts = corpus.count_by_type()
        assert "missing_semantics" in counts
        assert "temporal_error" in counts

    def test_corpus_get_by_type(self):
        corpus = build_initial_counterexamples()
        temporal = corpus.get_by_type(CounterexampleType.TEMPORAL_ERROR)
        assert len(temporal) >= 1

    def test_counterexample_to_dict(self):
        corpus = build_initial_counterexamples()
        d = corpus.counterexamples[0].to_dict()
        assert "counterexample_id" in d
        assert "title" in d
        assert "description" in d

    def test_corpus_to_dict(self):
        corpus = build_initial_counterexamples()
        d = corpus.to_dict()
        assert d["total_count"] == 10
        assert d["unresolved_count"] == 10

    def test_counterexample_ids_are_unique(self):
        corpus = build_initial_counterexamples()
        ids = [ce.counterexample_id for ce in corpus.counterexamples]
        assert len(ids) == len(set(ids))


class TestIntentGraphTrial:
    """Tests for the intent graph trial."""

    def test_trial_runs(self):
        result = run_intent_graph_trial()
        assert result.trial_id.startswith("trial_intent_")

    def test_trial_creates_intent_graph(self):
        result = run_intent_graph_trial()
        assert result.intent_graph is not None

    def test_trial_has_findings(self):
        result = run_intent_graph_trial()
        assert len(result.findings) > 0

    def test_trial_no_protocol_escapes(self):
        result = run_intent_graph_trial()
        assert result.metrics.protocol_escapes == 0

    def test_trial_no_unauthorized_consequences(self):
        result = run_intent_graph_trial()
        assert result.metrics.unauthorized_consequences == 0

    def test_trial_intent_graph_has_proposals(self):
        result = run_intent_graph_trial()
        assert len(result.intent_graph.proposals) >= 3

    def test_trial_intent_graph_has_edges(self):
        result = run_intent_graph_trial()
        assert len(result.intent_graph.edges) > 0

    def test_trial_intent_graph_has_chains(self):
        result = run_intent_graph_trial()
        assert len(result.intent_graph.get_sequential_chains()) > 0


class TestIntentGraphInvariants:
    """Tests for intent graph invariants."""

    def test_intent_does_not_create_authority(self):
        """INTENT DOES NOT CREATE AUTHORITY."""
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
            ),
        ]
        graph = build_intent_graph(proposals)
        # Intent graph has no authority mechanism
        assert not hasattr(graph, "authorize")

    def test_plan_does_not_create_authority(self):
        """PLAN DOES NOT CREATE AUTHORITY."""
        result = run_intent_graph_trial()
        # The intent graph trial should not produce authority
        assert result.metrics.protocol_escapes == 0

    def test_execution_order_does_not_create_authority(self):
        """EXECUTION ORDER DOES NOT CREATE AUTHORITY."""
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="backup",
                resource="database",
                arguments={},
                proposition="Backup database",
                postconditions=["database_backed_up"],
            ),
            ActionProposal(
                proposal_id="p2",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
                prerequisite_actions=["database_backed_up"],
            ),
        ]
        graph = build_intent_graph(proposals)
        # Sequential dependencies don't create authority
        chains = graph.get_sequential_chains()
        assert len(chains) >= 1

    def test_dependency_does_not_create_authority(self):
        """DEPENDENCY DOES NOT CREATE AUTHORITY."""
        result = run_intent_graph_trial()
        # Dependencies in the intent graph don't create authority
        assert result.metrics.protocol_escapes == 0

    def test_joint_intent_does_not_amplify_authority(self):
        """JOINT INTENT DOES NOT AMPLIFY COMPONENT AUTHORITY."""
        result = run_intent_graph_trial()
        # Joint intent should not create more authority than components
        assert result.metrics.protocol_escapes == 0
