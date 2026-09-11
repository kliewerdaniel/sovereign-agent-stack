"""Temporal infrastructure evolution for authority drift experiments.

Creates 10 temporal versions of the payment infrastructure, each with
a deliberate mutation that affects authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from research.examples.self_audit.authority_drift import AuthorityDriftEvent
from research.examples.self_audit.continuous_reconciliation import WorldState


@dataclass
class TemporalVersion:
    """A single temporal version of the infrastructure."""

    version_id: str
    timestamp: str
    description: str
    drift_event: Optional[AuthorityDriftEvent] = None
    world_state: WorldState = field(default_factory=lambda: WorldState(timestamp=""))


def build_temporal_versions() -> list[TemporalVersion]:
    """Build 10 temporal versions of the payment infrastructure."""
    versions = []

    # T0: Initial state - Provider A
    versions.append(TemporalVersion(
        version_id="T0",
        timestamp="2026-01-01T00:00:00Z",
        description="Initial state - Payment Gateway uses Provider A",
        world_state=WorldState(
            timestamp="2026-01-01T00:00:00Z",
            static_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_a", "type": "external"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_a", "type": "dependency"},
                ],
            },
            documented_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_a", "type": "external"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_a", "type": "dependency"},
                ],
            },
            runtime_topology={
                "actors": ["checkout"],
                "paths": [
                    {"id": "path_1", "actor": "checkout", "source": "checkout", "target": "payment_gateway"},
                    {"id": "path_2", "actor": "payment_gateway", "source": "payment_gateway", "target": "provider_a"},
                ],
            },
            authority_state={
                "actor": "payment_gateway",
                "component": "payment_gateway",
                "operation": "charge",
                "resource": "provider_a",
                "consequence_type": "payment",
                "authority_owner": "governance",
                "authority_basis": "explicit_delegation",
                "authorization_id": "auth_provider_a",
                "delegations": [
                    {
                        "id": "deleg_provider_a",
                        "actor": "payment_gateway",
                        "target": "provider_a",
                        "expires_at": "2027-01-01T00:00:00Z",
                    }
                ],
            },
            governance_state={
                "policies": [
                    {"id": "policy_1", "actor": "payment_gateway", "action": "charge", "resource": "provider_a"}
                ],
                "delegations": [
                    {"id": "deleg_provider_a", "actor": "payment_gateway", "target": "provider_a", "expires_at": "2027-01-01T00:00:00Z"}
                ],
            },
            provenance_state={
                "records": [
                    {"id": "prov_1", "type": "delegation", "actor": "governance", "target": "payment_gateway"},
                ]
            },
        ),
    ))

    # T1: Provider A -> Provider B
    versions.append(TemporalVersion(
        version_id="T1",
        timestamp="2026-02-01T00:00:00Z",
        description="Provider replacement - Payment Gateway now uses Provider B",
        drift_event=AuthorityDriftEvent(
            event_id="event_T1",
            timestamp="2026-02-01T00:00:00Z",
            event_type="provider_replacement",
            description="Provider A replaced by Provider B",
            affected_actor="payment_gateway",
            affected_component="payment_gateway",
            previous_state={"provider": "provider_a"},
            new_state={"provider": "provider_b"},
        ),
        world_state=WorldState(
            timestamp="2026-02-01T00:00:00Z",
            static_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_b", "type": "external"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_b", "type": "dependency"},
                ],
            },
            documented_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_a", "type": "external"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_a", "type": "dependency"},
                ],
            },
            runtime_topology={
                "actors": ["checkout"],
                "paths": [
                    {"id": "path_1", "actor": "checkout", "source": "checkout", "target": "payment_gateway"},
                    {"id": "path_2", "actor": "payment_gateway", "source": "payment_gateway", "target": "provider_b"},
                ],
            },
            authority_state={
                "actor": "payment_gateway",
                "component": "payment_gateway",
                "operation": "charge",
                "resource": "provider_b",
                "consequence_type": "payment",
                "authority_owner": "governance",
                "authority_basis": "explicit_delegation",
                "authorization_id": "auth_provider_a",  # Still references old provider!
                "delegations": [
                    {
                        "id": "deleg_provider_a",
                        "actor": "payment_gateway",
                        "target": "provider_a",
                        "expires_at": "2027-01-01T00:00:00Z",
                    }
                ],
            },
            governance_state={
                "policies": [
                    {"id": "policy_1", "actor": "payment_gateway", "action": "charge", "resource": "provider_a"}
                ],
                "delegations": [
                    {"id": "deleg_provider_a", "actor": "payment_gateway", "target": "provider_a", "expires_at": "2027-01-01T00:00:00Z"}
                ],
            },
            provenance_state={
                "records": [
                    {"id": "prov_1", "type": "delegation", "actor": "governance", "target": "payment_gateway"},
                    {"id": "prov_2", "type": "provider_change", "actor": "admin", "from": "provider_a", "to": "provider_b"},
                ]
            },
        ),
    ))

    # T2: Credential rotated
    versions.append(TemporalVersion(
        version_id="T2",
        timestamp="2026-03-01T00:00:00Z",
        description="Credential rotated for Provider B",
        drift_event=AuthorityDriftEvent(
            event_id="event_T2",
            timestamp="2026-03-01T00:00:00Z",
            event_type="credential_rotation",
            description="Provider B credentials rotated",
            affected_actor="payment_gateway",
            affected_component="credential_store",
            previous_state={"credential": "old_key"},
            new_state={"credential": "new_key"},
        ),
        world_state=WorldState(
            timestamp="2026-03-01T00:00:00Z",
            static_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_b", "type": "external"},
                    {"id": "credential_store", "type": "service"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_b", "type": "dependency"},
                    {"source": "payment_gateway", "target": "credential_store", "type": "call"},
                ],
            },
            documented_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_a", "type": "external"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_a", "type": "dependency"},
                ],
            },
            runtime_topology={
                "actors": ["checkout"],
                "paths": [
                    {"id": "path_1", "actor": "checkout", "source": "checkout", "target": "payment_gateway"},
                    {"id": "path_2", "actor": "payment_gateway", "source": "payment_gateway", "target": "provider_b"},
                    {"id": "path_3", "actor": "payment_gateway", "source": "payment_gateway", "target": "credential_store"},
                ],
            },
            authority_state={
                "actor": "payment_gateway",
                "component": "payment_gateway",
                "operation": "charge",
                "resource": "provider_b",
                "consequence_type": "payment",
                "authority_owner": "governance",
                "authority_basis": "explicit_delegation",
                "authorization_id": "auth_provider_b",
                "delegations": [
                    {
                        "id": "deleg_provider_b",
                        "actor": "payment_gateway",
                        "target": "provider_b",
                        "expires_at": "2027-01-01T00:00:00Z",
                    }
                ],
            },
            governance_state={
                "policies": [
                    {"id": "policy_1", "actor": "payment_gateway", "action": "charge", "resource": "provider_b"}
                ],
                "delegations": [
                    {"id": "deleg_provider_b", "actor": "payment_gateway", "target": "provider_b", "expires_at": "2027-01-01T00:00:00Z"}
                ],
            },
            provenance_state={
                "records": [
                    {"id": "prov_1", "type": "delegation", "actor": "governance", "target": "payment_gateway"},
                    {"id": "prov_2", "type": "provider_change", "actor": "admin", "from": "provider_a", "to": "provider_b"},
                    {"id": "prov_3", "type": "credential_rotation", "actor": "admin", "credential": "new_key"},
                ]
            },
        ),
    ))

    # T3: Feature flag activates Provider B
    versions.append(TemporalVersion(
        version_id="T3",
        timestamp="2026-04-01T00:00:00Z",
        description="Feature flag activates Provider B for all merchants",
        drift_event=AuthorityDriftEvent(
            event_id="event_T3",
            timestamp="2026-04-01T00:00:00Z",
            event_type="feature_flag_activation",
            description="Feature flag 'use_provider_b' activated",
            affected_actor="payment_gateway",
            affected_component="feature_flag_service",
            previous_state={"flag": False},
            new_state={"flag": True},
        ),
        world_state=WorldState(
            timestamp="2026-04-01T00:00:00Z",
            static_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_b", "type": "external"},
                    {"id": "credential_store", "type": "service"},
                    {"id": "feature_flag_service", "type": "service"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_b", "type": "dependency"},
                    {"source": "payment_gateway", "target": "credential_store", "type": "call"},
                    {"source": "payment_gateway", "target": "feature_flag_service", "type": "call"},
                ],
            },
            documented_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_a", "type": "external"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_a", "type": "dependency"},
                ],
            },
            runtime_topology={
                "actors": ["checkout"],
                "paths": [
                    {"id": "path_1", "actor": "checkout", "source": "checkout", "target": "payment_gateway"},
                    {"id": "path_2", "actor": "payment_gateway", "source": "payment_gateway", "target": "provider_b"},
                    {"id": "path_3", "actor": "payment_gateway", "source": "payment_gateway", "target": "credential_store"},
                    {"id": "path_4", "actor": "payment_gateway", "source": "payment_gateway", "target": "feature_flag_service"},
                ],
            },
            authority_state={
                "actor": "payment_gateway",
                "component": "payment_gateway",
                "operation": "charge",
                "resource": "provider_b",
                "consequence_type": "payment",
                "authority_owner": "governance",
                "authority_basis": "explicit_delegation",
                "authorization_id": "auth_provider_b",
                "delegations": [
                    {
                        "id": "deleg_provider_b",
                        "actor": "payment_gateway",
                        "target": "provider_b",
                        "expires_at": "2027-01-01T00:00:00Z",
                    }
                ],
            },
            governance_state={
                "policies": [
                    {"id": "policy_1", "actor": "payment_gateway", "action": "charge", "resource": "provider_b"},
                    {"id": "policy_2", "actor": "feature_flag_service", "flag": "use_provider_b", "enabled": True},
                ],
                "delegations": [
                    {"id": "deleg_provider_b", "actor": "payment_gateway", "target": "provider_b", "expires_at": "2027-01-01T00:00:00Z"}
                ],
            },
            provenance_state={
                "records": [
                    {"id": "prov_1", "type": "delegation", "actor": "governance", "target": "payment_gateway"},
                    {"id": "prov_2", "type": "provider_change", "actor": "admin", "from": "provider_a", "to": "provider_b"},
                    {"id": "prov_3", "type": "credential_rotation", "actor": "admin", "credential": "new_key"},
                    {"id": "prov_4", "type": "feature_flag", "actor": "admin", "flag": "use_provider_b", "enabled": True},
                ]
            },
        ),
    ))

    # T4: Background worker introduced
    versions.append(TemporalVersion(
        version_id="T4",
        timestamp="2026-05-01T00:00:00Z",
        description="Background worker introduced for async settlement",
        drift_event=AuthorityDriftEvent(
            event_id="event_T4",
            timestamp="2026-05-01T00:00:00Z",
            event_type="undocumented_worker",
            description="Background worker introduced without documentation",
            affected_actor="worker",
            affected_component="background_worker",
            previous_state={"worker": None},
            new_state={"worker": "active"},
        ),
        world_state=WorldState(
            timestamp="2026-05-01T00:00:00Z",
            static_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_b", "type": "external"},
                    {"id": "credential_store", "type": "service"},
                    {"id": "feature_flag_service", "type": "service"},
                    {"id": "worker", "type": "service"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_b", "type": "dependency"},
                    {"source": "payment_gateway", "target": "credential_store", "type": "call"},
                    {"source": "payment_gateway", "target": "feature_flag_service", "type": "call"},
                    {"source": "worker", "target": "payment_gateway", "type": "call"},
                ],
            },
            documented_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_a", "type": "external"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_a", "type": "dependency"},
                ],
            },
            runtime_topology={
                "actors": ["checkout", "worker"],
                "paths": [
                    {"id": "path_1", "actor": "checkout", "source": "checkout", "target": "payment_gateway"},
                    {"id": "path_2", "actor": "payment_gateway", "source": "payment_gateway", "target": "provider_b"},
                    {"id": "path_3", "actor": "payment_gateway", "source": "payment_gateway", "target": "credential_store"},
                    {"id": "path_4", "actor": "payment_gateway", "source": "payment_gateway", "target": "feature_flag_service"},
                    {"id": "path_5", "actor": "worker", "source": "worker", "target": "payment_gateway"},
                ],
            },
            authority_state={
                "actor": "payment_gateway",
                "component": "payment_gateway",
                "operation": "charge",
                "resource": "provider_b",
                "consequence_type": "payment",
                "authority_owner": "governance",
                "authority_basis": "explicit_delegation",
                "authorization_id": "auth_provider_b",
                "delegations": [
                    {
                        "id": "deleg_provider_b",
                        "actor": "payment_gateway",
                        "target": "provider_b",
                        "expires_at": "2027-01-01T00:00:00Z",
                    }
                ],
            },
            governance_state={
                "policies": [
                    {"id": "policy_1", "actor": "payment_gateway", "action": "charge", "resource": "provider_b"},
                    {"id": "policy_2", "actor": "feature_flag_service", "flag": "use_provider_b", "enabled": True},
                ],
                "delegations": [
                    {"id": "deleg_provider_b", "actor": "payment_gateway", "target": "provider_b", "expires_at": "2027-01-01T00:00:00Z"}
                ],
            },
            provenance_state={
                "records": [
                    {"id": "prov_1", "type": "delegation", "actor": "governance", "target": "payment_gateway"},
                    {"id": "prov_2", "type": "provider_change", "actor": "admin", "from": "provider_a", "to": "provider_b"},
                    {"id": "prov_3", "type": "credential_rotation", "actor": "admin", "credential": "new_key"},
                    {"id": "prov_4", "type": "feature_flag", "actor": "admin", "flag": "use_provider_b", "enabled": True},
                ]
            },
        ),
    ))

    # T5: Worker receives subprocess capability
    versions.append(TemporalVersion(
        version_id="T5",
        timestamp="2026-06-01T00:00:00Z",
        description="Worker receives subprocess capability",
        drift_event=AuthorityDriftEvent(
            event_id="event_T5",
            timestamp="2026-06-01T00:00:00Z",
            event_type="subprocess_introduction",
            description="Worker now executes subprocesses",
            affected_actor="worker",
            affected_component="background_worker",
            previous_state={"subprocess": False},
            new_state={"subprocess": True},
        ),
        world_state=WorldState(
            timestamp="2026-06-01T00:00:00Z",
            static_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_b", "type": "external"},
                    {"id": "credential_store", "type": "service"},
                    {"id": "feature_flag_service", "type": "service"},
                    {"id": "worker", "type": "service"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_b", "type": "dependency"},
                    {"source": "payment_gateway", "target": "credential_store", "type": "call"},
                    {"source": "payment_gateway", "target": "feature_flag_service", "type": "call"},
                    {"source": "worker", "target": "payment_gateway", "type": "call"},
                    {"source": "worker", "target": "subprocess", "type": "call"},
                ],
            },
            documented_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_a", "type": "external"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_a", "type": "dependency"},
                ],
            },
            runtime_topology={
                "actors": ["checkout", "worker"],
                "paths": [
                    {"id": "path_1", "actor": "checkout", "source": "checkout", "target": "payment_gateway"},
                    {"id": "path_2", "actor": "payment_gateway", "source": "payment_gateway", "target": "provider_b"},
                    {"id": "path_3", "actor": "payment_gateway", "source": "payment_gateway", "target": "credential_store"},
                    {"id": "path_4", "actor": "payment_gateway", "source": "payment_gateway", "target": "feature_flag_service"},
                    {"id": "path_5", "actor": "worker", "source": "worker", "target": "payment_gateway"},
                    {"id": "path_6", "actor": "worker", "source": "worker", "target": "subprocess"},
                ],
            },
            authority_state={
                "actor": "payment_gateway",
                "component": "payment_gateway",
                "operation": "charge",
                "resource": "provider_b",
                "consequence_type": "payment",
                "authority_owner": "governance",
                "authority_basis": "explicit_delegation",
                "authorization_id": "auth_provider_b",
                "delegations": [
                    {
                        "id": "deleg_provider_b",
                        "actor": "payment_gateway",
                        "target": "provider_b",
                        "expires_at": "2027-01-01T00:00:00Z",
                    }
                ],
            },
            governance_state={
                "policies": [
                    {"id": "policy_1", "actor": "payment_gateway", "action": "charge", "resource": "provider_b"},
                    {"id": "policy_2", "actor": "feature_flag_service", "flag": "use_provider_b", "enabled": True},
                ],
                "delegations": [
                    {"id": "deleg_provider_b", "actor": "payment_gateway", "target": "provider_b", "expires_at": "2027-01-01T00:00:00Z"}
                ],
            },
            provenance_state={
                "records": [
                    {"id": "prov_1", "type": "delegation", "actor": "governance", "target": "payment_gateway"},
                    {"id": "prov_2", "type": "provider_change", "actor": "admin", "from": "provider_a", "to": "provider_b"},
                    {"id": "prov_3", "type": "credential_rotation", "actor": "admin", "credential": "new_key"},
                    {"id": "prov_4", "type": "feature_flag", "actor": "admin", "flag": "use_provider_b", "enabled": True},
                ]
            },
        ),
    ))

    # T6: Delegation expires
    versions.append(TemporalVersion(
        version_id="T6",
        timestamp="2026-07-01T00:00:00Z",
        description="Delegation to Provider B expires",
        drift_event=AuthorityDriftEvent(
            event_id="event_T6",
            timestamp="2026-07-01T00:00:00Z",
            event_type="delegation_expiration",
            description="Delegation to Provider B expired",
            affected_actor="payment_gateway",
            affected_component="payment_gateway",
            previous_state={"delegation": "active"},
            new_state={"delegation": "expired"},
        ),
        world_state=WorldState(
            timestamp="2026-07-01T00:00:00Z",
            static_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_b", "type": "external"},
                    {"id": "credential_store", "type": "service"},
                    {"id": "feature_flag_service", "type": "service"},
                    {"id": "worker", "type": "service"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_b", "type": "dependency"},
                    {"source": "payment_gateway", "target": "credential_store", "type": "call"},
                    {"source": "payment_gateway", "target": "feature_flag_service", "type": "call"},
                    {"source": "worker", "target": "payment_gateway", "type": "call"},
                    {"source": "worker", "target": "subprocess", "type": "call"},
                ],
            },
            documented_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_a", "type": "external"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_a", "type": "dependency"},
                ],
            },
            runtime_topology={
                "actors": ["checkout", "worker"],
                "paths": [
                    {"id": "path_1", "actor": "checkout", "source": "checkout", "target": "payment_gateway"},
                    {"id": "path_2", "actor": "payment_gateway", "source": "payment_gateway", "target": "provider_b"},
                    {"id": "path_3", "actor": "payment_gateway", "source": "payment_gateway", "target": "credential_store"},
                    {"id": "path_4", "actor": "payment_gateway", "source": "payment_gateway", "target": "feature_flag_service"},
                    {"id": "path_5", "actor": "worker", "source": "worker", "target": "payment_gateway"},
                    {"id": "path_6", "actor": "worker", "source": "worker", "target": "subprocess"},
                ],
            },
            authority_state={
                "actor": "payment_gateway",
                "component": "payment_gateway",
                "operation": "charge",
                "resource": "provider_b",
                "consequence_type": "payment",
                "authority_owner": "governance",
                "authority_basis": "explicit_delegation",
                "authorization_id": "auth_provider_b",
                "delegations": [
                    {
                        "id": "deleg_provider_b",
                        "actor": "payment_gateway",
                        "target": "provider_b",
                        "expires_at": "2026-06-30T00:00:00Z",  # EXPIRED
                    }
                ],
            },
            governance_state={
                "policies": [
                    {"id": "policy_1", "actor": "payment_gateway", "action": "charge", "resource": "provider_b"},
                    {"id": "policy_2", "actor": "feature_flag_service", "flag": "use_provider_b", "enabled": True},
                ],
                "delegations": [
                    {"id": "deleg_provider_b", "actor": "payment_gateway", "target": "provider_b", "expires_at": "2026-06-30T00:00:00Z"}
                ],
            },
            provenance_state={
                "records": [
                    {"id": "prov_1", "type": "delegation", "actor": "governance", "target": "payment_gateway"},
                    {"id": "prov_2", "type": "provider_change", "actor": "admin", "from": "provider_a", "to": "provider_b"},
                    {"id": "prov_3", "type": "credential_rotation", "actor": "admin", "credential": "new_key"},
                    {"id": "prov_4", "type": "feature_flag", "actor": "admin", "flag": "use_provider_b", "enabled": True},
                ]
            },
        ),
    ))

    # T7: Governance policy changes
    versions.append(TemporalVersion(
        version_id="T7",
        timestamp="2026-08-01T00:00:00Z",
        description="Governance policy changes - Provider B now prohibited",
        drift_event=AuthorityDriftEvent(
            event_id="event_T7",
            timestamp="2026-08-01T00:00:00Z",
            event_type="governance_policy_modification",
            description="Policy changed to prohibit Provider B",
            affected_actor="payment_gateway",
            affected_component="payment_gateway",
            previous_state={"policy": "allow_provider_b"},
            new_state={"policy": "prohibit_provider_b"},
        ),
        world_state=WorldState(
            timestamp="2026-08-01T00:00:00Z",
            static_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_b", "type": "external"},
                    {"id": "credential_store", "type": "service"},
                    {"id": "feature_flag_service", "type": "service"},
                    {"id": "worker", "type": "service"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_b", "type": "dependency"},
                    {"source": "payment_gateway", "target": "credential_store", "type": "call"},
                    {"source": "payment_gateway", "target": "feature_flag_service", "type": "call"},
                    {"source": "worker", "target": "payment_gateway", "type": "call"},
                    {"source": "worker", "target": "subprocess", "type": "call"},
                ],
            },
            documented_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_a", "type": "external"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_a", "type": "dependency"},
                ],
            },
            runtime_topology={
                "actors": ["checkout", "worker"],
                "paths": [
                    {"id": "path_1", "actor": "checkout", "source": "checkout", "target": "payment_gateway"},
                    {"id": "path_2", "actor": "payment_gateway", "source": "payment_gateway", "target": "provider_b"},
                    {"id": "path_3", "actor": "payment_gateway", "source": "payment_gateway", "target": "credential_store"},
                    {"id": "path_4", "actor": "payment_gateway", "source": "payment_gateway", "target": "feature_flag_service"},
                    {"id": "path_5", "actor": "worker", "source": "worker", "target": "payment_gateway"},
                    {"id": "path_6", "actor": "worker", "source": "worker", "target": "subprocess"},
                ],
            },
            authority_state={
                "actor": "payment_gateway",
                "component": "payment_gateway",
                "operation": "charge",
                "resource": "provider_b",
                "consequence_type": "payment",
                "authority_owner": "governance",
                "authority_basis": "explicit_delegation",
                "authorization_id": "auth_provider_b",
                "delegations": [
                    {
                        "id": "deleg_provider_b",
                        "actor": "payment_gateway",
                        "target": "provider_b",
                        "expires_at": "2026-06-30T00:00:00Z",
                    }
                ],
            },
            governance_state={
                "policies": [
                    {"id": "policy_1", "actor": "payment_gateway", "action": "charge", "resource": "provider_b", "effect": "prohibit"},
                    {"id": "policy_2", "actor": "feature_flag_service", "flag": "use_provider_b", "enabled": True},
                ],
                "delegations": [
                    {"id": "deleg_provider_b", "actor": "payment_gateway", "target": "provider_b", "expires_at": "2026-06-30T00:00:00Z"}
                ],
            },
            provenance_state={
                "records": [
                    {"id": "prov_1", "type": "delegation", "actor": "governance", "target": "payment_gateway"},
                    {"id": "prov_2", "type": "provider_change", "actor": "admin", "from": "provider_a", "to": "provider_b"},
                    {"id": "prov_3", "type": "credential_rotation", "actor": "admin", "credential": "new_key"},
                    {"id": "prov_4", "type": "feature_flag", "actor": "admin", "flag": "use_provider_b", "enabled": True},
                    {"id": "prov_5", "type": "policy_change", "actor": "governance", "policy": "prohibit_provider_b"},
                ]
            },
        ),
    ))

    # T8: Legacy processor reactivated
    versions.append(TemporalVersion(
        version_id="T8",
        timestamp="2026-09-01T00:00:00Z",
        description="Legacy processor reactivated via feature flag",
        drift_event=AuthorityDriftEvent(
            event_id="event_T8",
            timestamp="2026-09-01T00:00:00Z",
            event_type="legacy_path_reactivation",
            description="Legacy processor reactivated via feature flag",
            affected_actor="payment_gateway",
            affected_component="legacy_processor",
            previous_state={"legacy": False},
            new_state={"legacy": True},
        ),
        world_state=WorldState(
            timestamp="2026-09-01T00:00:00Z",
            static_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_b", "type": "external"},
                    {"id": "credential_store", "type": "service"},
                    {"id": "feature_flag_service", "type": "service"},
                    {"id": "worker", "type": "service"},
                    {"id": "legacy_processor", "type": "service"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_b", "type": "dependency"},
                    {"source": "payment_gateway", "target": "credential_store", "type": "call"},
                    {"source": "payment_gateway", "target": "feature_flag_service", "type": "call"},
                    {"source": "worker", "target": "payment_gateway", "type": "call"},
                    {"source": "worker", "target": "subprocess", "type": "call"},
                    {"source": "payment_gateway", "target": "legacy_processor", "type": "call"},
                ],
            },
            documented_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_a", "type": "external"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_a", "type": "dependency"},
                ],
            },
            runtime_topology={
                "actors": ["checkout", "worker"],
                "paths": [
                    {"id": "path_1", "actor": "checkout", "source": "checkout", "target": "payment_gateway"},
                    {"id": "path_2", "actor": "payment_gateway", "source": "payment_gateway", "target": "provider_b"},
                    {"id": "path_3", "actor": "payment_gateway", "source": "payment_gateway", "target": "credential_store"},
                    {"id": "path_4", "actor": "payment_gateway", "source": "payment_gateway", "target": "feature_flag_service"},
                    {"id": "path_5", "actor": "worker", "source": "worker", "target": "payment_gateway"},
                    {"id": "path_6", "actor": "worker", "source": "worker", "target": "subprocess"},
                    {"id": "path_7", "actor": "payment_gateway", "source": "payment_gateway", "target": "legacy_processor"},
                ],
            },
            authority_state={
                "actor": "payment_gateway",
                "component": "payment_gateway",
                "operation": "charge",
                "resource": "provider_b",
                "consequence_type": "payment",
                "authority_owner": "governance",
                "authority_basis": "explicit_delegation",
                "authorization_id": "auth_provider_b",
                "delegations": [
                    {
                        "id": "deleg_provider_b",
                        "actor": "payment_gateway",
                        "target": "provider_b",
                        "expires_at": "2026-06-30T00:00:00Z",
                    }
                ],
            },
            governance_state={
                "policies": [
                    {"id": "policy_1", "actor": "payment_gateway", "action": "charge", "resource": "provider_b", "effect": "prohibit"},
                    {"id": "policy_2", "actor": "feature_flag_service", "flag": "use_provider_b", "enabled": True},
                ],
                "delegations": [
                    {"id": "deleg_provider_b", "actor": "payment_gateway", "target": "provider_b", "expires_at": "2026-06-30T00:00:00Z"}
                ],
            },
            provenance_state={
                "records": [
                    {"id": "prov_1", "type": "delegation", "actor": "governance", "target": "payment_gateway"},
                    {"id": "prov_2", "type": "provider_change", "actor": "admin", "from": "provider_a", "to": "provider_b"},
                    {"id": "prov_3", "type": "credential_rotation", "actor": "admin", "credential": "new_key"},
                    {"id": "prov_4", "type": "feature_flag", "actor": "admin", "flag": "use_provider_b", "enabled": True},
                    {"id": "prov_5", "type": "policy_change", "actor": "governance", "policy": "prohibit_provider_b"},
                ]
            },
        ),
    ))

    # T9: Documentation updated but runtime remains divergent
    versions.append(TemporalVersion(
        version_id="T9",
        timestamp="2026-10-01T00:00:00Z",
        description="Documentation updated but runtime remains divergent",
        drift_event=AuthorityDriftEvent(
            event_id="event_T9",
            timestamp="2026-10-01T00:00:00Z",
            event_type="documentation_update",
            description="Documentation updated to match some runtime paths",
            affected_actor="",
            affected_component="",
            previous_state={"documentation": "outdated"},
            new_state={"documentation": "partially_updated"},
        ),
        world_state=WorldState(
            timestamp="2026-10-01T00:00:00Z",
            static_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_b", "type": "external"},
                    {"id": "credential_store", "type": "service"},
                    {"id": "feature_flag_service", "type": "service"},
                    {"id": "worker", "type": "service"},
                    {"id": "legacy_processor", "type": "service"},
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_b", "type": "dependency"},
                    {"source": "payment_gateway", "target": "credential_store", "type": "call"},
                    {"source": "payment_gateway", "target": "feature_flag_service", "type": "call"},
                    {"source": "worker", "target": "payment_gateway", "type": "call"},
                    {"source": "worker", "target": "subprocess", "type": "call"},
                    {"source": "payment_gateway", "target": "legacy_processor", "type": "call"},
                ],
            },
            documented_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "payment_gateway", "type": "service"},
                    {"id": "provider_b", "type": "external"},  # Updated
                    {"id": "credential_store", "type": "service"},  # Added
                ],
                "edges": [
                    {"source": "checkout", "target": "payment_gateway", "type": "call"},
                    {"source": "payment_gateway", "target": "provider_b", "type": "dependency"},  # Updated
                    {"source": "payment_gateway", "target": "credential_store", "type": "call"},  # Added
                ],
            },
            runtime_topology={
                "actors": ["checkout", "worker"],
                "paths": [
                    {"id": "path_1", "actor": "checkout", "source": "checkout", "target": "payment_gateway"},
                    {"id": "path_2", "actor": "payment_gateway", "source": "payment_gateway", "target": "provider_b"},
                    {"id": "path_3", "actor": "payment_gateway", "source": "payment_gateway", "target": "credential_store"},
                    {"id": "path_4", "actor": "payment_gateway", "source": "payment_gateway", "target": "feature_flag_service"},
                    {"id": "path_5", "actor": "worker", "source": "worker", "target": "payment_gateway"},
                    {"id": "path_6", "actor": "worker", "source": "worker", "target": "subprocess"},
                    {"id": "path_7", "actor": "payment_gateway", "source": "payment_gateway", "target": "legacy_processor"},
                ],
            },
            authority_state={
                "actor": "payment_gateway",
                "component": "payment_gateway",
                "operation": "charge",
                "resource": "provider_b",
                "consequence_type": "payment",
                "authority_owner": "governance",
                "authority_basis": "explicit_delegation",
                "authorization_id": "auth_provider_b",
                "delegations": [
                    {
                        "id": "deleg_provider_b",
                        "actor": "payment_gateway",
                        "target": "provider_b",
                        "expires_at": "2026-06-30T00:00:00Z",
                    }
                ],
            },
            governance_state={
                "policies": [
                    {"id": "policy_1", "actor": "payment_gateway", "action": "charge", "resource": "provider_b", "effect": "prohibit"},
                    {"id": "policy_2", "actor": "feature_flag_service", "flag": "use_provider_b", "enabled": True},
                ],
                "delegations": [
                    {"id": "deleg_provider_b", "actor": "payment_gateway", "target": "provider_b", "expires_at": "2026-06-30T00:00:00Z"}
                ],
            },
            provenance_state={
                "records": [
                    {"id": "prov_1", "type": "delegation", "actor": "governance", "target": "payment_gateway"},
                    {"id": "prov_2", "type": "provider_change", "actor": "admin", "from": "provider_a", "to": "provider_b"},
                    {"id": "prov_3", "type": "credential_rotation", "actor": "admin", "credential": "new_key"},
                    {"id": "prov_4", "type": "feature_flag", "actor": "admin", "flag": "use_provider_b", "enabled": True},
                    {"id": "prov_5", "type": "policy_change", "actor": "governance", "policy": "prohibit_provider_b"},
                ]
            },
        ),
    ))

    return versions
