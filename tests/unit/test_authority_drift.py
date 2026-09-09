"""Tests for authority drift and continuous reconciliation."""

import pytest

from examples.self_audit.authority_drift import (
    AuthorityDelta,
    AuthorityDebt,
    AuthorityDebtItem,
    AuthorityDrift,
    AuthorityDriftEvent,
    AuthoritySnapshot,
    AuthorityStalenessFinding,
    AuthorityValidityInterval,
    ConsequenceType,
    DriftClassification,
    DriftFinding,
    DriftType,
    EpistemicState,
    GovernanceDelta,
    ProvenanceDelta,
    ReconciliationState,
    ReconciliationStatus,
    RuntimeDelta,
    TopologyDelta,
)
from examples.self_audit.continuous_reconciliation import (
    ContinuousAuthorityReconciler,
    WorldState,
)
from examples.self_audit.temporal_evolution import build_temporal_versions


class TestAuthoritySnapshot:
    """Tests for authority snapshot."""

    def test_snapshot_creation(self):
        snapshot = AuthoritySnapshot(
            snapshot_id="snap_001",
            timestamp="2026-01-01T00:00:00Z",
            actor="payment_gateway",
            component="payment_gateway",
            operation="charge",
            resource="provider_a",
            consequence_type=ConsequenceType.PAYMENT,
        )
        assert snapshot.snapshot_id == "snap_001"
        assert snapshot.actor == "payment_gateway"

    def test_snapshot_to_dict(self):
        snapshot = AuthoritySnapshot(
            snapshot_id="snap_001",
            timestamp="2026-01-01T00:00:00Z",
            actor="payment_gateway",
            component="payment_gateway",
            operation="charge",
            resource="provider_a",
            consequence_type=ConsequenceType.PAYMENT,
        )
        d = snapshot.to_dict()
        assert d["snapshot_id"] == "snap_001"
        assert d["actor"] == "payment_gateway"


class TestAuthorityDelta:
    """Tests for authority delta."""

    def test_delta_creation(self):
        prev = AuthoritySnapshot(
            snapshot_id="snap_prev",
            timestamp="2026-01-01T00:00:00Z",
            actor="payment_gateway",
            component="payment_gateway",
            operation="charge",
            resource="provider_a",
            consequence_type=ConsequenceType.PAYMENT,
        )
        curr = AuthoritySnapshot(
            snapshot_id="snap_curr",
            timestamp="2026-02-01T00:00:00Z",
            actor="payment_gateway",
            component="payment_gateway",
            operation="charge",
            resource="provider_b",
            consequence_type=ConsequenceType.PAYMENT,
        )
        delta = AuthorityDelta(
            delta_id="delta_001",
            previous_snapshot=prev,
            current_snapshot=curr,
            drift_type=DriftType.AUTHORITY_DRIFT,
            drift_classification=DriftClassification.SIGNIFICANT,
            changed_fields=["resource"],
            previous_authority="provider_a",
            current_authority="provider_b",
        )
        assert delta.delta_id == "delta_001"
        assert delta.drift_type == DriftType.AUTHORITY_DRIFT
        assert "resource" in delta.changed_fields

    def test_delta_to_dict(self):
        prev = AuthoritySnapshot(
            snapshot_id="snap_prev",
            timestamp="2026-01-01T00:00:00Z",
            actor="payment_gateway",
            component="payment_gateway",
            operation="charge",
            resource="provider_a",
            consequence_type=ConsequenceType.PAYMENT,
        )
        curr = AuthoritySnapshot(
            snapshot_id="snap_curr",
            timestamp="2026-02-01T00:00:00Z",
            actor="payment_gateway",
            component="payment_gateway",
            operation="charge",
            resource="provider_b",
            consequence_type=ConsequenceType.PAYMENT,
        )
        delta = AuthorityDelta(
            delta_id="delta_001",
            previous_snapshot=prev,
            current_snapshot=curr,
            drift_type=DriftType.AUTHORITY_DRIFT,
            drift_classification=DriftClassification.SIGNIFICANT,
            changed_fields=["resource"],
        )
        d = delta.to_dict()
        assert d["delta_id"] == "delta_001"
        assert d["drift_type"] == "authority_drift"


class TestAuthorityDrift:
    """Tests for authority drift."""

    def test_drift_creation(self):
        drift = AuthorityDrift(
            drift_id="drift_001",
            drift_type=DriftType.AUTHORITY_DRIFT,
            drift_classification=DriftClassification.SIGNIFICANT,
            description="Provider changed",
            affected_actor="payment_gateway",
            affected_component="payment_gateway",
            affected_consequence="payment",
            affected_resource="provider_b",
            previous_authority="provider_a",
            current_authority="provider_b",
        )
        assert drift.drift_id == "drift_001"
        assert drift.drift_type == DriftType.AUTHORITY_DRIFT

    def test_drift_to_dict(self):
        drift = AuthorityDrift(
            drift_id="drift_001",
            drift_type=DriftType.AUTHORITY_DRIFT,
            drift_classification=DriftClassification.SIGNIFICANT,
            description="Provider changed",
            affected_actor="payment_gateway",
            affected_component="payment_gateway",
            affected_consequence="payment",
            affected_resource="provider_b",
        )
        d = drift.to_dict()
        assert d["drift_id"] == "drift_001"
        assert d["drift_type"] == "authority_drift"


class TestAuthorityValidityInterval:
    """Tests for authority validity interval."""

    def test_valid_interval(self):
        interval = AuthorityValidityInterval(
            interval_id="int_001",
            authority_id="auth_001",
            valid_from="2026-01-01T00:00:00Z",
            valid_until="2027-01-01T00:00:00Z",
        )
        assert interval.is_valid_at

    def test_expired_interval(self):
        interval = AuthorityValidityInterval(
            interval_id="int_001",
            authority_id="auth_001",
            valid_from="2020-01-01T00:00:00Z",
            valid_until="2020-12-31T00:00:00Z",
        )
        assert not interval.is_valid_at

    def test_interval_to_dict(self):
        interval = AuthorityValidityInterval(
            interval_id="int_001",
            authority_id="auth_001",
            valid_from="2026-01-01T00:00:00Z",
        )
        d = interval.to_dict()
        assert d["interval_id"] == "int_001"
        assert d["is_valid_at"]


class TestAuthorityStalenessFinding:
    """Tests for authority staleness finding."""

    def test_staleness_creation(self):
        finding = AuthorityStalenessFinding(
            finding_id="stale_001",
            authority_id="auth_001",
            staleness_type="expired_delegation",
            description="Delegation expired",
            previous_state="active",
            current_state="expired",
            temporal_boundary="2026-06-30T00:00:00Z",
            affected_consequence="payment",
        )
        assert finding.finding_id == "stale_001"
        assert finding.staleness_type == "expired_delegation"

    def test_staleness_to_dict(self):
        finding = AuthorityStalenessFinding(
            finding_id="stale_001",
            authority_id="auth_001",
            staleness_type="expired_delegation",
            description="Delegation expired",
            previous_state="active",
            current_state="expired",
            temporal_boundary="2026-06-30T00:00:00Z",
            affected_consequence="payment",
        )
        d = finding.to_dict()
        assert d["finding_id"] == "stale_001"
        assert d["staleness_type"] == "expired_delegation"


class TestAuthorityDebt:
    """Tests for authority debt."""

    def test_debt_creation(self):
        debt = AuthorityDebt(debt_report_id="debt_001")
        assert debt.debt_report_id == "debt_001"
        assert debt.total_debt_items == 0

    def test_debt_with_items(self):
        item = AuthorityDebtItem(
            debt_id="debt_item_001",
            debt_type="documentation_runtime_divergence",
            description="Runtime path not documented",
            evidence=["Runtime: checkout -> payment_gateway"],
            scope="checkout -> payment_gateway",
            temporal_interval="2026-01-01T00:00:00Z",
            affected_consequence="payment",
            epistemic_status=EpistemicState.OBSERVED,
            resolution_requirements=["Document the path"],
        )
        debt = AuthorityDebt(
            debt_report_id="debt_001",
            documentation_runtime_divergence=[item],
        )
        assert debt.total_debt_items == 1

    def test_debt_to_dict(self):
        debt = AuthorityDebt(debt_report_id="debt_001")
        d = debt.to_dict()
        assert d["debt_report_id"] == "debt_001"
        assert d["total_debt_items"] == 0


class TestDriftFinding:
    """Tests for drift finding."""

    def test_finding_creation(self):
        finding = DriftFinding(
            finding_id="drift_001",
            drift_type=DriftType.AUTHORITY_DRIFT,
            drift_classification=DriftClassification.SIGNIFICANT,
            description="Provider changed",
            previous_state={"provider": "provider_a"},
            current_state={"provider": "provider_b"},
            temporal_boundary="2026-01-01T00:00:00Z -> 2026-02-01T00:00:00Z",
            affected_actor="payment_gateway",
            affected_component="payment_gateway",
            affected_consequence="payment",
            affected_resource="provider_b",
        )
        assert finding.finding_id == "drift_001"
        assert finding.drift_type == DriftType.AUTHORITY_DRIFT

    def test_finding_to_dict(self):
        finding = DriftFinding(
            finding_id="drift_001",
            drift_type=DriftType.AUTHORITY_DRIFT,
            drift_classification=DriftClassification.SIGNIFICANT,
            description="Provider changed",
            previous_state={"provider": "provider_a"},
            current_state={"provider": "provider_b"},
            temporal_boundary="2026-01-01T00:00:00Z -> 2026-02-01T00:00:00Z",
            affected_actor="payment_gateway",
            affected_component="payment_gateway",
            affected_consequence="payment",
            affected_resource="provider_b",
        )
        d = finding.to_dict()
        assert d["finding_id"] == "drift_001"
        assert d["drift_type"] == "authority_drift"


class TestReconciliationStatus:
    """Tests for reconciliation status."""

    def test_status_creation(self):
        status = ReconciliationStatus(
            status_id="rec_001",
            timestamp="2026-01-01T00:00:00Z",
            reconciliation_state=ReconciliationState.RECONCILED,
            current_authority_state={},
            historical_authority_state={},
        )
        assert status.status_id == "rec_001"
        assert status.reconciliation_state == ReconciliationState.RECONCILED

    def test_status_to_dict(self):
        status = ReconciliationStatus(
            status_id="rec_001",
            timestamp="2026-01-01T00:00:00Z",
            reconciliation_state=ReconciliationState.RECONCILED,
            current_authority_state={},
            historical_authority_state={},
        )
        d = status.to_dict()
        assert d["status_id"] == "rec_001"
        assert d["reconciliation_state"] == "reconciled"


class TestContinuousAuthorityReconciler:
    """Tests for continuous authority reconciler."""

    def test_reconcile_no_drift(self):
        reconciler = ContinuousAuthorityReconciler()
        world = WorldState(
            timestamp="2026-01-01T00:00:00Z",
            authority_state={"actor": "payment_gateway", "resource": "provider_a"},
        )
        status = reconciler.reconcile(world, world)
        assert status.reconciliation_state == ReconciliationState.RECONCILED

    def test_reconcile_with_drift(self):
        reconciler = ContinuousAuthorityReconciler()
        prev_world = WorldState(
            timestamp="2026-01-01T00:00:00Z",
            static_topology={
                "nodes": [{"id": "checkout"}],
                "edges": [{"source": "checkout", "target": "payment_gateway"}],
            },
            authority_state={"actor": "payment_gateway", "resource": "provider_a"},
        )
        curr_world = WorldState(
            timestamp="2026-02-01T00:00:00Z",
            static_topology={
                "nodes": [{"id": "checkout"}],
                "edges": [{"source": "checkout", "target": "payment_gateway"}],
            },
            authority_state={"actor": "payment_gateway", "resource": "provider_b"},
        )
        status = reconciler.reconcile(prev_world, curr_world)
        # Authority change detected
        assert status.reconciliation_state in (
            ReconciliationState.DRIFT_DETECTED,
            ReconciliationState.CONFLICT,
            ReconciliationState.PENDING_REVIEW,
        )

    def test_reconcile_with_runtime_drift(self):
        reconciler = ContinuousAuthorityReconciler()
        prev_world = WorldState(
            timestamp="2026-01-01T00:00:00Z",
            runtime_topology={"actors": ["checkout"], "paths": []},
        )
        curr_world = WorldState(
            timestamp="2026-02-01T00:00:00Z",
            runtime_topology={
                "actors": ["checkout", "worker"],
                "paths": [{"actor": "worker", "source": "worker", "target": "payment_gateway"}],
            },
        )
        status = reconciler.reconcile(prev_world, curr_world)
        assert status.reconciliation_state in (
            ReconciliationState.DRIFT_DETECTED,
            ReconciliationState.CONFLICT,
        )

    def test_reconcile_with_governance_drift(self):
        reconciler = ContinuousAuthorityReconciler()
        prev_world = WorldState(
            timestamp="2026-01-01T00:00:00Z",
            governance_state={"policies": [{"id": "policy_1"}]},
        )
        curr_world = WorldState(
            timestamp="2026-02-01T00:00:00Z",
            governance_state={
                "policies": [{"id": "policy_1"}, {"id": "policy_2"}],
            },
        )
        status = reconciler.reconcile(prev_world, curr_world)
        assert status.reconciliation_state in (
            ReconciliationState.DRIFT_DETECTED,
            ReconciliationState.CONFLICT,
        )

    def test_reconcile_produces_drift_findings(self):
        reconciler = ContinuousAuthorityReconciler()
        prev_world = WorldState(
            timestamp="2026-01-01T00:00:00Z",
            authority_state={"actor": "payment_gateway", "resource": "provider_a"},
        )
        curr_world = WorldState(
            timestamp="2026-02-01T00:00:00Z",
            authority_state={"actor": "payment_gateway", "resource": "provider_b"},
        )
        status = reconciler.reconcile(prev_world, curr_world)
        # Authority delta should be detected
        assert status.authority_delta is not None

    def test_reconcile_produces_authority_debt(self):
        reconciler = ContinuousAuthorityReconciler()
        prev_world = WorldState(
            timestamp="2026-01-01T00:00:00Z",
            documented_topology={
                "edges": [{"source": "checkout", "target": "payment_gateway"}],
            },
            runtime_topology={
                "paths": [
                    {"source": "checkout", "target": "payment_gateway"},
                    {"source": "payment_gateway", "target": "provider_b"},
                ],
            },
        )
        curr_world = WorldState(
            timestamp="2026-02-01T00:00:00Z",
            documented_topology={
                "edges": [{"source": "checkout", "target": "payment_gateway"}],
            },
            runtime_topology={
                "paths": [
                    {"source": "checkout", "target": "payment_gateway"},
                    {"source": "payment_gateway", "target": "provider_b"},
                ],
            },
        )
        status = reconciler.reconcile(prev_world, curr_world)
        assert status.authority_debt is not None

    def test_reconcile_detects_staleness(self):
        reconciler = ContinuousAuthorityReconciler()
        prev_world = WorldState(
            timestamp="2026-01-01T00:00:00Z",
            authority_state={
                "delegations": [
                    {"id": "deleg_1", "expires_at": "2027-01-01T00:00:00Z"}
                ],
            },
        )
        curr_world = WorldState(
            timestamp="2026-02-01T00:00:00Z",
            authority_state={
                "delegations": [
                    {"id": "deleg_1", "expires_at": "2026-01-15T00:00:00Z"}  # Expired
                ],
            },
        )
        status = reconciler.reconcile(prev_world, curr_world)
        assert len(status.stale_authority) > 0


class TestTemporalEvolution:
    """Tests for temporal infrastructure evolution."""

    def test_build_temporal_versions(self):
        versions = build_temporal_versions()
        assert len(versions) == 10

    def test_version_ids(self):
        versions = build_temporal_versions()
        expected_ids = [f"T{i}" for i in range(10)]
        actual_ids = [v.version_id for v in versions]
        assert actual_ids == expected_ids

    def test_each_version_has_world_state(self):
        versions = build_temporal_versions()
        for version in versions:
            assert version.world_state is not None
            assert version.world_state.timestamp == version.timestamp

    def test_T0_initial_state(self):
        versions = build_temporal_versions()
        t0 = versions[0]
        assert t0.version_id == "T0"
        # Provider A in T0
        assert any(
            e.get("target") == "provider_a"
            for e in t0.world_state.static_topology.get("edges", [])
        )

    def test_T1_provider_replaced(self):
        versions = build_temporal_versions()
        t1 = versions[1]
        assert t1.version_id == "T1"
        # Provider B in T1
        assert any(
            e.get("target") == "provider_b"
            for e in t1.world_state.static_topology.get("edges", [])
        )
        # Drift event recorded
        assert t1.drift_event is not None
        assert t1.drift_event.event_type == "provider_replacement"

    def test_T1_documentation_divergence(self):
        versions = build_temporal_versions()
        t1 = versions[1]
        # Documentation still says Provider A
        assert any(
            e.get("target") == "provider_a"
            for e in t1.world_state.documented_topology.get("edges", [])
        )
        # Runtime says Provider B
        assert any(
            e.get("target") == "provider_b"
            for e in t1.world_state.runtime_topology.get("paths", [])
        )

    def test_T6_delegation_expired(self):
        versions = build_temporal_versions()
        t6 = versions[6]
        assert t6.version_id == "T6"
        # Delegation should be expired
        delegations = t6.world_state.authority_state.get("delegations", [])
        assert len(delegations) > 0
        assert delegations[0].get("expires_at") == "2026-06-30T00:00:00Z"

    def test_T7_policy_prohibits(self):
        versions = build_temporal_versions()
        t7 = versions[7]
        assert t7.version_id == "T7"
        # Policy should prohibit Provider B
        policies = t7.world_state.governance_state.get("policies", [])
        assert any(p.get("effect") == "prohibit" for p in policies)

    def test_T9_documentation_partially_updated(self):
        versions = build_temporal_versions()
        t9 = versions[9]
        assert t9.version_id == "T9"
        # Documentation should mention Provider B
        assert any(
            e.get("target") == "provider_b"
            for e in t9.world_state.documented_topology.get("edges", [])
        )
        # But not worker, subprocess, legacy_processor
        doc_edges = t9.world_state.documented_topology.get("edges", [])
        doc_targets = {e.get("target") for e in doc_edges}
        assert "worker" not in doc_targets
        assert "subprocess" not in doc_targets
        assert "legacy_processor" not in doc_targets


class TestTemporalReconciliation:
    """Tests for temporal reconciliation across versions."""

    def test_reconcile_T0_T1_detects_drift(self):
        versions = build_temporal_versions()
        reconciler = ContinuousAuthorityReconciler()
        status = reconciler.reconcile(versions[0].world_state, versions[1].world_state)
        assert status.reconciliation_state != ReconciliationState.RECONCILED

    def test_reconcile_T5_T6_detects_staleness(self):
        versions = build_temporal_versions()
        reconciler = ContinuousAuthorityReconciler()
        status = reconciler.reconcile(versions[5].world_state, versions[6].world_state)
        assert len(status.stale_authority) > 0

    def test_reconcile_T6_T7_detects_governance_drift(self):
        versions = build_temporal_versions()
        reconciler = ContinuousAuthorityReconciler()
        status = reconciler.reconcile(versions[6].world_state, versions[7].world_state)
        assert status.reconciliation_state in (
            ReconciliationState.DRIFT_DETECTED,
            ReconciliationState.CONFLICT,
        )

    def test_reconcile_T8_T9_detects_documentation_divergence(self):
        versions = build_temporal_versions()
        reconciler = ContinuousAuthorityReconciler()
        status = reconciler.reconcile(versions[8].world_state, versions[9].world_state)
        # Documentation updated but runtime still divergent
        assert status.authority_debt is not None
        assert status.authority_debt.total_debt_items > 0

    def test_continuous_reconciliation_history(self):
        versions = build_temporal_versions()
        reconciler = ContinuousAuthorityReconciler()
        for i in range(len(versions) - 1):
            reconciler.reconcile(versions[i].world_state, versions[i + 1].world_state)
        assert len(reconciler.reconciliation_history) == 9

    def test_historical_snapshots_preserved(self):
        versions = build_temporal_versions()
        reconciler = ContinuousAuthorityReconciler()
        # Ingest all snapshots
        for version in versions:
            snapshot = AuthoritySnapshot(
                snapshot_id=f"snap_{version.version_id}",
                timestamp=version.timestamp,
                actor="payment_gateway",
                component="payment_gateway",
                operation="charge",
                resource=version.world_state.authority_state.get("resource", "unknown"),
                consequence_type=ConsequenceType.PAYMENT,
            )
            reconciler.ingest_snapshot(snapshot)
        assert len(reconciler.snapshots) == 10
