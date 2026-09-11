"""Continuous Authority Reconciler.

Ingests observations from multiple worlds and produces reconciliation status.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from research.examples.self_audit.authority_drift import (
    AuthorityDelta,
    AuthorityDebt,
    AuthorityDebtItem,
    AuthorityDrift,
    AuthorityDriftEvent,
    AuthoritySnapshot,
    AuthorityStalenessFinding,
    AuthorityValidityInterval,
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


@dataclass
class WorldState:
    """State of a single world at a point in time."""

    timestamp: str
    static_topology: dict[str, Any] = field(default_factory=dict)
    documented_topology: dict[str, Any] = field(default_factory=dict)
    runtime_topology: dict[str, Any] = field(default_factory=dict)
    authority_state: dict[str, Any] = field(default_factory=dict)
    governance_state: dict[str, Any] = field(default_factory=dict)
    provenance_state: dict[str, Any] = field(default_factory=dict)
    epistemic_state: dict[str, Any] = field(default_factory=dict)


class ContinuousAuthorityReconciler:
    """Continuously reconciles authority across worlds and time."""

    def __init__(self):
        self.snapshots: list[AuthoritySnapshot] = []
        self.drift_events: list[AuthorityDriftEvent] = []
        self.reconciliation_history: list[ReconciliationStatus] = []

    def ingest_snapshot(self, snapshot: AuthoritySnapshot):
        """Ingest a new authority snapshot."""
        self.snapshots.append(snapshot)

    def ingest_drift_event(self, event: AuthorityDriftEvent):
        """Ingest a drift event."""
        self.drift_events.append(event)

    def reconcile(
        self,
        previous_world: WorldState,
        current_world: WorldState,
    ) -> ReconciliationStatus:
        """Reconcile two world states."""
        # Compute deltas
        topology_delta = self._compute_topology_delta(previous_world, current_world)
        governance_delta = self._compute_governance_delta(previous_world, current_world)
        runtime_delta = self._compute_runtime_delta(previous_world, current_world)
        provenance_delta = self._compute_provenance_delta(previous_world, current_world)

        # Detect drift
        drift_findings = self._detect_drift(
            previous_world, current_world, topology_delta, governance_delta, runtime_delta, provenance_delta
        )

        # Compute authority delta
        authority_delta = self._compute_authority_delta(previous_world, current_world)

        # Detect staleness
        stale_authority = self._detect_staleness(current_world)

        # Compute authority debt
        authority_debt = self._compute_authority_debt(previous_world, current_world)

        # Determine reconciliation state
        reconciliation_state = self._determine_reconciliation_state(drift_findings, authority_delta)

        # Identify unresolved questions
        unresolved_questions = self._identify_unresolved_questions(
            previous_world, current_world, drift_findings
        )

        # Identify limitations
        limitations = self._identify_limitations()

        # Build provenance chain
        provenance_chain = self._build_provenance_chain()

        status = ReconciliationStatus(
            status_id=f"rec_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            reconciliation_state=reconciliation_state,
            current_authority_state=current_world.authority_state,
            historical_authority_state=previous_world.authority_state,
            authority_delta=authority_delta,
            drift_findings=drift_findings,
            authority_debt=authority_debt,
            stale_authority=stale_authority,
            unresolved_questions=unresolved_questions,
            limitations=limitations,
            provenance_chain=provenance_chain,
        )

        self.reconciliation_history.append(status)
        return status

    def _compute_topology_delta(
        self,
        previous: WorldState,
        current: WorldState,
    ) -> TopologyDelta:
        """Compute topology delta between two world states."""
        prev_edges = previous.static_topology.get("edges", [])
        curr_edges = current.static_topology.get("edges", [])

        added = [e for e in curr_edges if e not in prev_edges]
        removed = [e for e in prev_edges if e not in curr_edges]
        modified = []

        # Check for modified edges (same source/target but different properties)
        for prev_edge in prev_edges:
            for curr_edge in curr_edges:
                if (prev_edge.get("source") == curr_edge.get("source") and
                    prev_edge.get("target") == curr_edge.get("target") and
                    prev_edge != curr_edge):
                    modified.append({"previous": prev_edge, "current": curr_edge})

        prev_nodes = previous.static_topology.get("nodes", [])
        curr_nodes = current.static_topology.get("nodes", [])

        added_nodes = [n for n in curr_nodes if n not in prev_nodes]
        removed_nodes = [n for n in prev_nodes if n not in curr_nodes]

        return TopologyDelta(
            delta_id=f"topo_{uuid.uuid4().hex[:12]}",
            previous_timestamp=previous.timestamp,
            current_timestamp=current.timestamp,
            added_edges=added,
            removed_edges=removed,
            modified_edges=modified,
            added_nodes=added_nodes,
            removed_nodes=removed_nodes,
        )

    def _compute_governance_delta(
        self,
        previous: WorldState,
        current: WorldState,
    ) -> GovernanceDelta:
        """Compute governance delta between two world states."""
        prev_policies = previous.governance_state.get("policies", [])
        curr_policies = current.governance_state.get("policies", [])

        added_policies = [p for p in curr_policies if p not in prev_policies]
        removed_policies = [p for p in prev_policies if p not in curr_policies]
        modified_policies = []

        for prev_pol in prev_policies:
            for curr_pol in curr_policies:
                if (prev_pol.get("id") == curr_pol.get("id") and prev_pol != curr_pol):
                    modified_policies.append({"previous": prev_pol, "current": curr_pol})

        prev_delegations = previous.governance_state.get("delegations", [])
        curr_delegations = current.governance_state.get("delegations", [])

        added_delegations = [d for d in curr_delegations if d not in prev_delegations]
        removed_delegations = [d for d in prev_delegations if d not in curr_delegations]
        modified_delegations = []

        for prev_del in prev_delegations:
            for curr_del in curr_delegations:
                if (prev_del.get("id") == curr_del.get("id") and prev_del != curr_del):
                    modified_delegations.append({"previous": prev_del, "current": curr_del})

        return GovernanceDelta(
            delta_id=f"gov_{uuid.uuid4().hex[:12]}",
            previous_timestamp=previous.timestamp,
            current_timestamp=current.timestamp,
            added_policies=added_policies,
            removed_policies=removed_policies,
            modified_policies=modified_policies,
            added_delegations=added_delegations,
            removed_delegations=removed_delegations,
            modified_delegations=modified_delegations,
        )

    def _compute_runtime_delta(
        self,
        previous: WorldState,
        current: WorldState,
    ) -> RuntimeDelta:
        """Compute runtime delta between two world states."""
        prev_paths = previous.runtime_topology.get("paths", [])
        curr_paths = current.runtime_topology.get("paths", [])

        added_paths = [p for p in curr_paths if p not in prev_paths]
        removed_paths = [p for p in prev_paths if p not in curr_paths]
        modified_paths = []

        for prev_path in prev_paths:
            for curr_path in curr_paths:
                if (prev_path.get("id") == curr_path.get("id") and prev_path != curr_path):
                    modified_paths.append({"previous": prev_path, "current": curr_path})

        prev_actors = set(previous.runtime_topology.get("actors", []))
        curr_actors = set(current.runtime_topology.get("actors", []))

        new_actors = list(curr_actors - prev_actors)
        removed_actors = list(prev_actors - curr_actors)

        return RuntimeDelta(
            delta_id=f"runtime_{uuid.uuid4().hex[:12]}",
            previous_timestamp=previous.timestamp,
            current_timestamp=current.timestamp,
            added_paths=added_paths,
            removed_paths=removed_paths,
            modified_paths=modified_paths,
            new_actors=new_actors,
            removed_actors=removed_actors,
        )

    def _compute_provenance_delta(
        self,
        previous: WorldState,
        current: WorldState,
    ) -> ProvenanceDelta:
        """Compute provenance delta between two world states."""
        prev_records = previous.provenance_state.get("records", [])
        curr_records = current.provenance_state.get("records", [])

        added_records = [r for r in curr_records if r not in prev_records]
        removed_records = [r for r in prev_records if r not in curr_records]
        modified_records = []

        for prev_rec in prev_records:
            for curr_rec in curr_records:
                if (prev_rec.get("id") == curr_rec.get("id") and prev_rec != curr_rec):
                    modified_records.append({"previous": prev_rec, "current": curr_rec})

        # Check for missing records (referenced but not present)
        missing_records = []
        for record in curr_records:
            if record.get("references"):
                for ref in record["references"]:
                    if not any(r.get("id") == ref for r in curr_records):
                        missing_records.append(ref)

        return ProvenanceDelta(
            delta_id=f"prov_{uuid.uuid4().hex[:12]}",
            previous_timestamp=previous.timestamp,
            current_timestamp=current.timestamp,
            added_records=added_records,
            removed_records=removed_records,
            modified_records=modified_records,
            missing_records=missing_records,
        )

    def _detect_drift(
        self,
        previous: WorldState,
        current: WorldState,
        topology_delta: TopologyDelta,
        governance_delta: GovernanceDelta,
        runtime_delta: RuntimeDelta,
        provenance_delta: ProvenanceDelta,
    ) -> list[DriftFinding]:
        """Detect drift between two world states."""
        findings = []

        # Check for topology drift
        if topology_delta.added_edges or topology_delta.removed_edges or topology_delta.modified_edges:
            findings.append(DriftFinding(
                finding_id=f"drift_topo_{uuid.uuid4().hex[:12]}",
                drift_type=DriftType.IMPLEMENTATION_DRIFT,
                drift_classification=DriftClassification.SIGNIFICANT,
                description="Static topology has changed",
                previous_state={"topology": previous.static_topology},
                current_state={"topology": current.static_topology},
                temporal_boundary=f"{previous.timestamp} -> {current.timestamp}",
                affected_actor="",
                affected_component="",
                affected_consequence="",
                affected_resource="",
                evidence=[f"Added: {len(topology_delta.added_edges)}", f"Removed: {len(topology_delta.removed_edges)}"],
            ))

        # Check for runtime drift
        if runtime_delta.added_paths or runtime_delta.removed_paths:
            findings.append(DriftFinding(
                finding_id=f"drift_runtime_{uuid.uuid4().hex[:12]}",
                drift_type=DriftType.RUNTIME_DRIFT,
                drift_classification=DriftClassification.SIGNIFICANT,
                description="Runtime paths have changed",
                previous_state={"runtime": previous.runtime_topology},
                current_state={"runtime": current.runtime_topology},
                temporal_boundary=f"{previous.timestamp} -> {current.timestamp}",
                affected_actor="",
                affected_component="",
                affected_consequence="",
                affected_resource="",
                evidence=[f"Added: {len(runtime_delta.added_paths)}", f"Removed: {len(runtime_delta.removed_paths)}"],
            ))

        # Check for governance drift
        if governance_delta.added_policies or governance_delta.removed_policies:
            findings.append(DriftFinding(
                finding_id=f"drift_gov_{uuid.uuid4().hex[:12]}",
                drift_type=DriftType.GOVERNANCE_DRIFT,
                drift_classification=DriftClassification.CRITICAL,
                description="Governance policies have changed",
                previous_state={"governance": previous.governance_state},
                current_state={"governance": current.governance_state},
                temporal_boundary=f"{previous.timestamp} -> {current.timestamp}",
                affected_actor="",
                affected_component="",
                affected_consequence="",
                affected_resource="",
                evidence=[f"Added: {len(governance_delta.added_policies)}", f"Removed: {len(governance_delta.removed_policies)}"],
            ))

        # Check for provenance drift
        if provenance_delta.missing_records:
            findings.append(DriftFinding(
                finding_id=f"drift_prov_{uuid.uuid4().hex[:12]}",
                drift_type=DriftType.PROVENANCE_DRIFT,
                drift_classification=DriftClassification.SIGNIFICANT,
                description="Provenance records are missing",
                previous_state={"provenance": previous.provenance_state},
                current_state={"provenance": current.provenance_state},
                temporal_boundary=f"{previous.timestamp} -> {current.timestamp}",
                affected_actor="",
                affected_component="",
                affected_consequence="",
                affected_resource="",
                evidence=[f"Missing: {len(provenance_delta.missing_records)}"],
            ))

        return findings

    def _compute_authority_delta(
        self,
        previous: WorldState,
        current: WorldState,
    ) -> Optional[AuthorityDelta]:
        """Compute authority delta between two world states."""
        prev_auth = previous.authority_state
        curr_auth = current.authority_state

        if prev_auth == curr_auth:
            return None

        # Find changed fields
        changed_fields = []
        all_keys = set(prev_auth.keys()) | set(curr_auth.keys())
        for key in all_keys:
            if prev_auth.get(key) != curr_auth.get(key):
                changed_fields.append(key)

        # Create snapshots
        prev_snapshot = AuthoritySnapshot(
            snapshot_id=f"snap_prev_{uuid.uuid4().hex[:12]}",
            timestamp=previous.timestamp,
            actor=prev_auth.get("actor", ""),
            component=prev_auth.get("component", ""),
            operation=prev_auth.get("operation", ""),
            resource=prev_auth.get("resource", ""),
            consequence_type=prev_auth.get("consequence_type", "external_effect"),
            authority_owner=prev_auth.get("authority_owner"),
            authority_basis=prev_auth.get("authority_basis"),
            authorization_id=prev_auth.get("authorization_id"),
        )

        curr_snapshot = AuthoritySnapshot(
            snapshot_id=f"snap_curr_{uuid.uuid4().hex[:12]}",
            timestamp=current.timestamp,
            actor=curr_auth.get("actor", ""),
            component=curr_auth.get("component", ""),
            operation=curr_auth.get("operation", ""),
            resource=curr_auth.get("resource", ""),
            consequence_type=curr_auth.get("consequence_type", "external_effect"),
            authority_owner=curr_auth.get("authority_owner"),
            authority_basis=curr_auth.get("authority_basis"),
            authorization_id=curr_auth.get("authorization_id"),
        )

        return AuthorityDelta(
            delta_id=f"auth_delta_{uuid.uuid4().hex[:12]}",
            previous_snapshot=prev_snapshot,
            current_snapshot=curr_snapshot,
            drift_type=DriftType.AUTHORITY_DRIFT,
            drift_classification=DriftClassification.SIGNIFICANT,
            changed_fields=changed_fields,
            previous_authority=prev_auth.get("authority_basis"),
            current_authority=curr_auth.get("authority_basis"),
            previous_governance=prev_auth.get("governance_policy"),
            current_governance=curr_auth.get("governance_policy"),
        )

    def _detect_staleness(self, current_world: WorldState) -> list[AuthorityStalenessFinding]:
        """Detect stale authority in the current world state."""
        stale = []
        authority_state = current_world.authority_state

        # Check for expired delegations
        delegations = authority_state.get("delegations", [])
        for delegation in delegations:
            if delegation.get("expires_at"):
                expires = delegation["expires_at"]
                now = datetime.utcnow().isoformat()
                if expires < now:
                    stale.append(AuthorityStalenessFinding(
                        finding_id=f"stale_{uuid.uuid4().hex[:12]}",
                        authority_id=delegation.get("id", ""),
                        staleness_type="expired_delegation",
                        description=f"Delegation {delegation.get('id')} expired at {expires}",
                        previous_state="active",
                        current_state="expired",
                        temporal_boundary=expires,
                        affected_consequence=delegation.get("consequence_type", ""),
                        evidence=[f"Expiration: {expires}"],
                    ))

        return stale

    def _compute_authority_debt(
        self,
        previous: WorldState,
        current: WorldState,
    ) -> AuthorityDebt:
        """Compute authority debt between two world states."""
        debt_items = {
            "documentation_runtime_divergence": [],
            "runtime_governance_divergence": [],
            "governance_provenance_gap": [],
            "stale_delegation": [],
            "unbounded_consequence": [],
            "unresolved_owner": [],
            "missing_reconstruction": [],
        }

        # Check documentation vs runtime divergence
        doc_topology = current.documented_topology
        runtime_topology = current.runtime_topology

        doc_edges = set((e.get("source"), e.get("target")) for e in doc_topology.get("edges", []))
        runtime_edges = set((e.get("source"), e.get("target")) for e in runtime_topology.get("paths", []))

        divergence = runtime_edges - doc_edges
        for source, target in divergence:
            debt_items["documentation_runtime_divergence"].append(AuthorityDebtItem(
                debt_id=f"debt_doc_runtime_{uuid.uuid4().hex[:12]}",
                debt_type="documentation_runtime_divergence",
                description=f"Runtime path {source} -> {target} not documented",
                evidence=[f"Runtime: {source} -> {target}"],
                scope=f"{source} -> {target}",
                temporal_interval=current.timestamp,
                affected_consequence="",
                epistemic_status=EpistemicState.OBSERVED,
                resolution_requirements=["Document the path", "Verify authority"],
            ))

        # Check runtime vs governance divergence
        gov_state = current.governance_state
        for path in runtime_topology.get("paths", []):
            actor = path.get("actor", "")
            if not any(d.get("actor") == actor for d in gov_state.get("delegations", [])):
                if not any(p.get("actor") == actor for p in gov_state.get("policies", [])):
                    debt_items["runtime_governance_divergence"].append(AuthorityDebtItem(
                        debt_id=f"debt_runtime_gov_{uuid.uuid4().hex[:12]}",
                        debt_type="runtime_governance_divergence",
                        description=f"Actor {actor} has runtime path but no governance",
                        evidence=[f"Actor: {actor}"],
                        scope=actor,
                        temporal_interval=current.timestamp,
                        affected_consequence="",
                        epistemic_status=EpistemicState.OBSERVED,
                        resolution_requirements=["Add governance for actor"],
                    ))

        # Check stale delegations
        for delegation in current.authority_state.get("delegations", []):
            if delegation.get("expires_at"):
                expires = delegation["expires_at"]
                now = datetime.utcnow().isoformat()
                if expires < now:
                    debt_items["stale_delegation"].append(AuthorityDebtItem(
                        debt_id=f"debt_stale_del_{uuid.uuid4().hex[:12]}",
                        debt_type="stale_delegation",
                        description=f"Delegation {delegation.get('id')} expired",
                        evidence=[f"Expiration: {expires}"],
                        scope=delegation.get("id", ""),
                        temporal_interval=f"{expires} -> {current.timestamp}",
                        affected_consequence=delegation.get("consequence_type", ""),
                        epistemic_status=EpistemicState.OBSERVED,
                        resolution_requirements=["Renew or revoke delegation"],
                    ))

        return AuthorityDebt(
            debt_report_id=f"debt_{uuid.uuid4().hex[:12]}",
            documentation_runtime_divergence=debt_items["documentation_runtime_divergence"],
            runtime_governance_divergence=debt_items["runtime_governance_divergence"],
            governance_provenance_gap=debt_items["governance_provenance_gap"],
            stale_delegation=debt_items["stale_delegation"],
            unbounded_consequence=debt_items["unbounded_consequence"],
            unresolved_owner=debt_items["unresolved_owner"],
            missing_reconstruction=debt_items["missing_reconstruction"],
        )

    def _determine_reconciliation_state(
        self,
        drift_findings: list[DriftFinding],
        authority_delta: Optional[AuthorityDelta],
    ) -> ReconciliationState:
        """Determine the reconciliation state."""
        if not drift_findings and not authority_delta:
            return ReconciliationState.RECONCILED

        # Check authority delta
        if authority_delta:
            if authority_delta.drift_classification == DriftClassification.CRITICAL:
                return ReconciliationState.CONFLICT
            elif authority_delta.drift_classification == DriftClassification.SIGNIFICANT:
                return ReconciliationState.DRIFT_DETECTED

        critical_findings = [f for f in drift_findings if f.drift_classification == DriftClassification.CRITICAL]
        if critical_findings:
            return ReconciliationState.CONFLICT

        significant_findings = [f for f in drift_findings if f.drift_classification == DriftClassification.SIGNIFICANT]
        if significant_findings:
            return ReconciliationState.DRIFT_DETECTED

        inconclusive_findings = [f for f in drift_findings if f.drift_classification == DriftClassification.INCONCLUSIVE]
        if inconclusive_findings:
            return ReconciliationState.INCONCLUSIVE

        return ReconciliationState.PENDING_REVIEW

    def _identify_unresolved_questions(
        self,
        previous: WorldState,
        current: WorldState,
        drift_findings: list[DriftFinding],
    ) -> list[str]:
        """Identify unresolved questions."""
        questions = []

        for finding in drift_findings:
            if finding.drift_type == DriftType.AUTHORITY_DRIFT:
                questions.append("What is the new authority basis?")
                questions.append("Is the new authority intentional?")
            elif finding.drift_type == DriftType.GOVERNANCE_DRIFT:
                questions.append("What governance decision caused the change?")
                questions.append("Is the new governance compatible with existing authority?")
            elif finding.drift_type == DriftType.RUNTIME_DRIFT:
                questions.append("Is the new runtime path authorized?")
                questions.append("What is the authority basis for the new path?")

        return questions

    def _identify_limitations(self) -> list[str]:
        """Identify limitations of the reconciliation."""
        return [
            "Reconciliation is based on provided observations only",
            "Historical snapshots may be incomplete",
            "Runtime traces may not cover all paths",
            "Governance state may not reflect actual enforcement",
        ]

    def _build_provenance_chain(self) -> list[str]:
        """Build provenance chain for the reconciliation."""
        chain = []
        for snapshot in self.snapshots[-5:]:  # Last 5 snapshots
            chain.append(f"snapshot:{snapshot.snapshot_id}")
        for event in self.drift_events[-5:]:  # Last 5 drift events
            chain.append(f"event:{event.event_id}")
        return chain
