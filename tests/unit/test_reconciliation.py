"""Tests for static-dynamic reconciliation engine."""

import pytest

from examples.self_audit.reconciliation import (
    AuthorityGraphEdge,
    EpistemicState,
    ReconciliationClassification,
    ReconciliationEngine,
    ReconciliationResult,
    ReconstructionState,
    RuntimeAuthorityReconstructor,
    RuntimeEvent,
    StaticHypothesis,
    TraceBasedAuthorityGraph,
)


class TestStaticHypothesis:
    """Tests for static hypothesis structure."""

    def test_hypothesis_creation(self):
        h = StaticHypothesis(
            hypothesis_id="hyp_0001",
            source="src/sas/argopack.py",
            target="subprocess.run",
            operation="subprocess_execution",
            consequence_type="external_consequential",
            static_evidence="subprocess.run(cmd, ...)",
            expected_authority_boundary="none",
            expected_capability="none",
            expected_authorization="none",
            expected_provenance="none",
            predicted_classification="authority_escape",
            confidence=0.6,
            source_location="src/sas/argopack.py",
            target_location="line 119",
            alternatives=[],
        )
        assert h.hypothesis_id == "hyp_0001"
        assert h.source == "src/sas/argopack.py"
        assert h.target == "subprocess.run"

    def test_hypothesis_to_dict(self):
        h = StaticHypothesis(
            hypothesis_id="hyp_0001",
            source="src/sas/argopack.py",
            target="subprocess.run",
            operation="subprocess_execution",
            consequence_type="external_consequential",
            static_evidence="subprocess.run(cmd, ...)",
            expected_authority_boundary="none",
            expected_capability="none",
            expected_authorization="none",
            expected_provenance="none",
            predicted_classification="authority_escape",
            confidence=0.6,
            source_location="src/sas/argopack.py",
            target_location="line 119",
            alternatives=[],
        )
        d = h.to_dict()
        assert d["hypothesis_id"] == "hyp_0001"
        assert d["source"] == "src/sas/argopack.py"
        assert d["target"] == "subprocess.run"


class TestRuntimeEvent:
    """Tests for runtime event structure."""

    def test_event_creation(self):
        e = RuntimeEvent(
            event_id="evt_001",
            timestamp="2026-09-09T00:00:00",
            event_type="subprocess_create",
            actor="test",
            component="argopack",
            operation="subprocess.run",
            resource="python -m sas --help",
            consequence_type="external_consequential",
            parent_event=None,
            call_path=[],
            authority_context={},
            capability_id=None,
            authorization_id=None,
            provenance_id=None,
            environment="test",
            process_id=12345,
            thread_id=67890,
            result="exit_code=0",
            scope="test",
            limitations="test event",
        )
        assert e.event_id == "evt_001"
        assert e.actor == "test"
        assert e.operation == "subprocess.run"

    def test_event_to_dict(self):
        e = RuntimeEvent(
            event_id="evt_001",
            timestamp="2026-09-09T00:00:00",
            event_type="subprocess_create",
            actor="test",
            component="argopack",
            operation="subprocess.run",
            resource="python -m sas --help",
            consequence_type="external_consequential",
            parent_event=None,
            call_path=[],
            authority_context={},
            capability_id=None,
            authorization_id=None,
            provenance_id=None,
            environment="test",
            process_id=12345,
            thread_id=67890,
            result="exit_code=0",
            scope="test",
            limitations="test event",
        )
        d = e.to_dict()
        assert d["event_id"] == "evt_001"
        assert d["actor"] == "test"
        assert d["operation"] == "subprocess.run"


class TestReconciliationEngine:
    """Tests for the reconciliation engine."""

    def test_reconcile_no_runtime_evidence(self):
        h = StaticHypothesis(
            hypothesis_id="hyp_0001",
            source="src/sas/argopack.py",
            target="subprocess.run",
            operation="subprocess_execution",
            consequence_type="state_transforming",
            static_evidence="open(write)",
            expected_authority_boundary="internal_state",
            expected_capability="none",
            expected_authorization="none",
            expected_provenance="none",
            predicted_classification="static_false_positive",
            confidence=0.8,
            source_location="src/sas/registry.py",
            target_location="line 10",
            alternatives=[],
        )
        engine = ReconciliationEngine([h], [])
        results = engine.reconcile()
        assert len(results) == 1
        assert results[0].classification == ReconciliationClassification.STATIC_FALSE_POSITIVE

    def test_reconcile_with_authority_escape(self):
        h = StaticHypothesis(
            hypothesis_id="hyp_0001",
            source="src/sas/argopack.py",
            target="subprocess.run",
            operation="subprocess_execution",
            consequence_type="external_consequential",
            static_evidence="subprocess.run(cmd, ...)",
            expected_authority_boundary="none",
            expected_capability="none",
            expected_authorization="none",
            expected_provenance="none",
            predicted_classification="authority_escape",
            confidence=0.6,
            source_location="src/sas/argopack.py",
            target_location="line 119",
            alternatives=[],
        )
        e = RuntimeEvent(
            event_id="evt_001",
            timestamp="2026-09-09T00:00:00",
            event_type="subprocess_create",
            actor="test",
            component="argopack",
            operation="subprocess.run",
            resource="python -m sas --help",
            consequence_type="external_consequential",
            parent_event=None,
            call_path=[],
            authority_context={},
            capability_id=None,
            authorization_id=None,
            provenance_id=None,
            environment="test",
            process_id=12345,
            thread_id=67890,
            result="exit_code=0",
            scope="test",
            limitations="test event",
        )
        engine = ReconciliationEngine([h], [e])
        results = engine.reconcile()
        assert len(results) == 1
        assert results[0].classification == ReconciliationClassification.AUTHORITY_ESCAPE
        assert results[0].epistemic_state == EpistemicState.UNAUTHORIZED

    def test_reconcile_with_controlled_authority(self):
        h = StaticHypothesis(
            hypothesis_id="hyp_0001",
            source="src/sas/quant/broker/adapter.py",
            target="submit_trade",
            operation="broker_call",
            consequence_type="external_consequential",
            static_evidence="submit_trade(trade, ...)",
            expected_authority_boundary="capability_bound",
            expected_capability="CapabilityBoundBroker",
            expected_authorization="AuthorizationArtifact",
            expected_provenance="ProvenanceRecord",
            predicted_classification="authority_controlled",
            confidence=0.75,
            source_location="src/sas/quant/broker/adapter.py",
            target_location="line 50",
            alternatives=[],
        )
        e = RuntimeEvent(
            event_id="evt_001",
            timestamp="2026-09-09T00:00:00",
            event_type="broker_call",
            actor="test",
            component="broker",
            operation="submit_trade",
            resource="AAPL",
            consequence_type="external_consequential",
            parent_event=None,
            call_path=[],
            authority_context={},
            capability_id="cap_123",
            authorization_id="auth_456",
            provenance_id="prov_789",
            environment="test",
            process_id=12345,
            thread_id=67890,
            result="success",
            scope="test",
            limitations="test event",
        )
        engine = ReconciliationEngine([h], [e])
        results = engine.reconcile()
        assert len(results) == 1
        assert results[0].classification == ReconciliationClassification.AUTHORITY_CONTROLLED
        assert results[0].epistemic_state == EpistemicState.AUTHORIZED

    def test_reconcile_multiple_hypotheses(self):
        h1 = StaticHypothesis(
            hypothesis_id="hyp_0001",
            source="src/sas/argopack.py",
            target="subprocess.run",
            operation="subprocess_execution",
            consequence_type="external_consequential",
            static_evidence="subprocess.run(cmd, ...)",
            expected_authority_boundary="none",
            expected_capability="none",
            expected_authorization="none",
            expected_provenance="none",
            predicted_classification="authority_escape",
            confidence=0.6,
            source_location="src/sas/argopack.py",
            target_location="line 119",
            alternatives=[],
        )
        h2 = StaticHypothesis(
            hypothesis_id="hyp_0002",
            source="src/sas/registry.py",
            target="open(write)",
            operation="filesystem_mutation",
            consequence_type="state_transforming",
            static_evidence="open(path, 'w')",
            expected_authority_boundary="internal_state",
            expected_capability="none",
            expected_authorization="none",
            expected_provenance="none",
            predicted_classification="static_false_positive",
            confidence=0.8,
            source_location="src/sas/registry.py",
            target_location="line 10",
            alternatives=[],
        )
        engine = ReconciliationEngine([h1, h2], [])
        results = engine.reconcile()
        assert len(results) == 2
        assert results[0].classification == ReconciliationClassification.STATIC_ONLY
        assert results[1].classification == ReconciliationClassification.STATIC_FALSE_POSITIVE

    def test_to_dict(self):
        h = StaticHypothesis(
            hypothesis_id="hyp_0001",
            source="src/sas/argopack.py",
            target="subprocess.run",
            operation="subprocess_execution",
            consequence_type="external_consequential",
            static_evidence="subprocess.run(cmd, ...)",
            expected_authority_boundary="none",
            expected_capability="none",
            expected_authorization="none",
            expected_provenance="none",
            predicted_classification="authority_escape",
            confidence=0.6,
            source_location="src/sas/argopack.py",
            target_location="line 119",
            alternatives=[],
        )
        engine = ReconciliationEngine([h], [])
        engine.reconcile()
        d = engine.to_dict()
        assert d["total_reconciliations"] == 1
        assert "by_classification" in d["summary"]
        assert "by_epistemic_state" in d["summary"]


class TestTraceBasedAuthorityGraph:
    """Tests for trace-based authority graph builder."""

    def test_build_call_graph(self):
        e = RuntimeEvent(
            event_id="evt_001",
            timestamp="2026-09-09T00:00:00",
            event_type="subprocess_create",
            actor="test",
            component="argopack",
            operation="subprocess.run",
            resource="python -m sas --help",
            consequence_type="external_consequential",
            parent_event="evt_000",
            call_path=["evt_000"],
            authority_context={},
            capability_id=None,
            authorization_id=None,
            provenance_id=None,
            environment="test",
            process_id=12345,
            thread_id=67890,
            result="exit_code=0",
            scope="test",
            limitations="test event",
        )
        builder = TraceBasedAuthorityGraph([e])
        graphs = builder.build_graphs()
        assert len(graphs["call_graph"]) == 1
        assert graphs["call_graph"][0].source == "evt_000"
        assert graphs["call_graph"][0].target == "evt_001"

    def test_build_consequence_graph(self):
        e = RuntimeEvent(
            event_id="evt_001",
            timestamp="2026-09-09T00:00:00",
            event_type="subprocess_create",
            actor="test",
            component="argopack",
            operation="subprocess.run",
            resource="python -m sas --help",
            consequence_type="external_consequential",
            parent_event=None,
            call_path=[],
            authority_context={},
            capability_id=None,
            authorization_id=None,
            provenance_id=None,
            environment="test",
            process_id=12345,
            thread_id=67890,
            result="exit_code=0",
            scope="test",
            limitations="test event",
        )
        builder = TraceBasedAuthorityGraph([e])
        graphs = builder.build_graphs()
        assert len(graphs["consequence_graph"]) == 1
        assert graphs["consequence_graph"][0].consequence_type == "external_consequential"

    def test_build_authority_graph(self):
        e = RuntimeEvent(
            event_id="evt_001",
            timestamp="2026-09-09T00:00:00",
            event_type="subprocess_create",
            actor="test",
            component="argopack",
            operation="subprocess.run",
            resource="python -m sas --help",
            consequence_type="external_consequential",
            parent_event=None,
            call_path=[],
            authority_context={},
            capability_id="cap_123",
            authorization_id="auth_456",
            provenance_id="prov_789",
            environment="test",
            process_id=12345,
            thread_id=67890,
            result="exit_code=0",
            scope="test",
            limitations="test event",
        )
        builder = TraceBasedAuthorityGraph([e])
        graphs = builder.build_graphs()
        assert len(graphs["authority_graph"]) == 1
        assert graphs["authority_graph"][0].capability_id == "cap_123"

    def test_build_provenance_graph(self):
        e = RuntimeEvent(
            event_id="evt_001",
            timestamp="2026-09-09T00:00:00",
            event_type="subprocess_create",
            actor="test",
            component="argopack",
            operation="subprocess.run",
            resource="python -m sas --help",
            consequence_type="external_consequential",
            parent_event=None,
            call_path=[],
            authority_context={},
            capability_id=None,
            authorization_id=None,
            provenance_id="prov_789",
            environment="test",
            process_id=12345,
            thread_id=67890,
            result="exit_code=0",
            scope="test",
            limitations="test event",
        )
        builder = TraceBasedAuthorityGraph([e])
        graphs = builder.build_graphs()
        assert len(graphs["provenance_graph"]) == 1
        assert graphs["provenance_graph"][0].provenance_id == "prov_789"

    def test_to_dict(self):
        e = RuntimeEvent(
            event_id="evt_001",
            timestamp="2026-09-09T00:00:00",
            event_type="subprocess_create",
            actor="test",
            component="argopack",
            operation="subprocess.run",
            resource="python -m sas --help",
            consequence_type="external_consequential",
            parent_event=None,
            call_path=[],
            authority_context={},
            capability_id=None,
            authorization_id=None,
            provenance_id=None,
            environment="test",
            process_id=12345,
            thread_id=67890,
            result="exit_code=0",
            scope="test",
            limitations="test event",
        )
        builder = TraceBasedAuthorityGraph([e])
        builder.build_graphs()
        d = builder.to_dict()
        assert "call_graph" in d
        assert "consequence_graph" in d
        assert "authority_graph" in d
        assert "provenance_graph" in d
        assert "summary" in d


class TestRuntimeAuthorityReconstructor:
    """Tests for runtime authority reconstruction."""

    def test_reconstruct_unauthorized_event(self):
        e = RuntimeEvent(
            event_id="evt_001",
            timestamp="2026-09-09T00:00:00",
            event_type="subprocess_create",
            actor="test",
            component="argopack",
            operation="subprocess.run",
            resource="python -m sas --help",
            consequence_type="external_consequential",
            parent_event=None,
            call_path=[],
            authority_context={},
            capability_id=None,
            authorization_id=None,
            provenance_id=None,
            environment="test",
            process_id=12345,
            thread_id=67890,
            result="exit_code=0",
            scope="test",
            limitations="test event",
        )
        reconstructor = RuntimeAuthorityReconstructor([e])
        results = reconstructor.reconstruct_all()
        assert len(results) == 1
        assert results[0]["reconstruction_state"] == ReconstructionState.UNAUTHORIZED
        assert "authorization" in results[0]["missing_links"]
        assert "capability" in results[0]["missing_links"]
        assert "provenance" in results[0]["missing_links"]

    def test_reconstruct_authorized_event(self):
        e = RuntimeEvent(
            event_id="evt_001",
            timestamp="2026-09-09T00:00:00",
            event_type="broker_call",
            actor="test",
            component="broker",
            operation="submit_trade",
            resource="AAPL",
            consequence_type="external_consequential",
            parent_event=None,
            call_path=[],
            authority_context={},
            capability_id="cap_123",
            authorization_id="auth_456",
            provenance_id="prov_789",
            environment="test",
            process_id=12345,
            thread_id=67890,
            result="success",
            scope="test",
            limitations="test event",
        )
        reconstructor = RuntimeAuthorityReconstructor([e])
        results = reconstructor.reconstruct_all()
        assert len(results) == 1
        # With capability + authorization + provenance, state is AUTHORIZED_AND_RECONSTRUCTIBLE
        # but governance, sovereign_root, receipt are still missing
        assert results[0]["reconstruction_state"] in (
            ReconstructionState.AUTHORIZED_AND_RECONSTRUCTIBLE,
            ReconstructionState.AUTHORIZED_BUT_NOT_RECONSTRUCTIBLE,
        )
        assert len(results[0]["missing_links"]) == 4  # sovereign_root, policy, governance, receipt

    def test_reconstruct_non_consequential_event(self):
        e = RuntimeEvent(
            event_id="evt_001",
            timestamp="2026-09-09T00:00:00",
            event_type="filesystem_read",
            actor="test",
            component="config",
            operation="open(read)",
            resource="config.yaml",
            consequence_type="informational",
            parent_event=None,
            call_path=[],
            authority_context={},
            capability_id=None,
            authorization_id=None,
            provenance_id=None,
            environment="test",
            process_id=12345,
            thread_id=67890,
            result="success",
            scope="test",
            limitations="test event",
        )
        reconstructor = RuntimeAuthorityReconstructor([e])
        results = reconstructor.reconstruct_all()
        assert len(results) == 0  # Non-consequential events are not reconstructed

    def test_to_dict(self):
        e = RuntimeEvent(
            event_id="evt_001",
            timestamp="2026-09-09T00:00:00",
            event_type="subprocess_create",
            actor="test",
            component="argopack",
            operation="subprocess.run",
            resource="python -m sas --help",
            consequence_type="external_consequential",
            parent_event=None,
            call_path=[],
            authority_context={},
            capability_id=None,
            authorization_id=None,
            provenance_id=None,
            environment="test",
            process_id=12345,
            thread_id=67890,
            result="exit_code=0",
            scope="test",
            limitations="test event",
        )
        reconstructor = RuntimeAuthorityReconstructor([e])
        reconstructor.reconstruct_all()
        d = reconstructor.to_dict()
        assert d["total_reconstructions"] == 1
        assert "reconstructions" in d
        assert "summary" in d
