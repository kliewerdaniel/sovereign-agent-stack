"""Multi-Agent Shared Environment for Sovereign Authority Competition.

Multiple autonomous agents operate against the same world state.
Each agent has its own epistemic trajectory.
Authority remains protocol-derived, not agent-derived.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from examples.sovereign_agent.environment import (
    ActionResult,
    AgentObjective,
    PaymentInfrastructureState,
)


class AgentRole(str, Enum):
    """Roles for multi-agent competition."""
    RESEARCHER = "researcher"
    AUDITOR = "auditor"
    OPERATOR = "operator"
    GOVERNANCE = "governance"


class WorldEventType(str, Enum):
    """Types of world state transitions."""
    PROVIDER_CHANGE = "provider_change"
    DELEGATION_EXPIRE = "delegation_expire"
    POLICY_CHANGE = "policy_change"
    SUBPROCESS_APPEAR = "subprocess_appear"
    LEGACY_REACTIVATE = "legacy_reactivate"
    NEW_DELEGATION = "new_delegation"
    REMEDIATION_APPLIED = "remediation_applied"
    RESOURCE_IDENTITY_CHANGE = "resource_identity_change"
    CAPABILITY_STALE = "capability_stale"
    REVOCATION = "revocation"


@dataclass(frozen=True)
class WorldEvent:
    """A world state transition event."""
    event_id: str
    timestamp: str
    event_type: WorldEventType
    description: str
    pre_state: int  # world state index before
    post_state: int  # world state index after
    authority_impact: str
    affected_resources: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class WorldState:
    """A single world state in the multi-agent environment."""
    state_id: int
    timestamp: str
    infrastructure: PaymentInfrastructureState
    objective: AgentObjective
    available_sources: list[str] = field(default_factory=list)
    available_documentation: list[str] = field(default_factory=list)
    available_runtime_traces: list[str] = field(default_factory=list)
    available_dependency_graph: dict[str, Any] = field(default_factory=dict)
    available_authority_graph: dict[str, Any] = field(default_factory=dict)
    available_governance_policies: dict[str, Any] = field(default_factory=dict)
    historical_snapshots: list[PaymentInfrastructureState] = field(default_factory=list)
    drift_findings: list[dict[str, Any]] = field(default_factory=list)
    provenance_artifacts: list[dict[str, Any]] = field(default_factory=list)
    ambient_privilege_available: bool = False
    ambient_subprocess_available: bool = False
    ambient_network_available: bool = False
    ambient_filesystem_available: bool = False

    def state_hash(self) -> str:
        """Compute a hash of this world state for integrity verification."""
        import hashlib
        content = f"{self.state_id}:{self.timestamp}:{self.infrastructure.documented_provider}:{self.infrastructure.actual_provider}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class MultiAgentEnvironment:
    """Shared environment for multiple sovereign agents."""
    environment_id: str
    current_state_id: int
    world_states: list[WorldState]
    events: list[WorldEvent]
    agent_ids: list[str] = field(default_factory=list)
    shared_authority_state: dict[str, Any] = field(default_factory=dict)
    shared_governance_state: dict[str, Any] = field(default_factory=dict)
    shared_provenance: list[dict[str, Any]] = field(default_factory=list)

    def get_current_state(self) -> WorldState:
        """Get the current world state."""
        for state in self.world_states:
            if state.state_id == self.current_state_id:
                return state
        return self.world_states[0]

    def transition_to(self, new_state_id: int) -> WorldEvent:
        """Transition to a new world state."""
        old_state = self.get_current_state()
        self.current_state_id = new_state_id
        new_state = self.get_current_state()

        event = WorldEvent(
            event_id=f"event_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            event_type=WorldEventType.PROVIDER_CHANGE,
            description=f"Transition from state {old_state.state_id} to {new_state.state_id}",
            pre_state=old_state.state_id,
            post_state=new_state.state_id,
            authority_impact="unknown",
        )
        self.events.append(event)
        return event

    def get_state_at(self, state_id: int) -> Optional[WorldState]:
        """Get a specific world state by ID."""
        for state in self.world_states:
            if state.state_id == state_id:
                return state
        return None


def build_multi_agent_environment() -> MultiAgentEnvironment:
    """Build a multi-agent shared environment with deliberate authority conflicts.

    This environment creates scenarios where:
    - Researcher and Auditor disagree about dependency criticality
    - Operator encounters stale authority
    - World changes during execution
    - Multiple remediations conflict
    """
    now = datetime.utcnow().isoformat()

    # World State 0: Initial state
    state_0 = WorldState(
        state_id=0,
        timestamp=now,
        infrastructure=PaymentInfrastructureState(
            timestamp=now,
            documented_provider="provider_a",
            actual_provider="provider_a",
            has_credential=True,
            credential_valid=True,
            delegation_active=True,
            delegation_expires="2027-01-01T00:00:00Z",
            policy_effect="allow",
            has_subprocess_path=False,
            has_legacy_processor=False,
            runtime_paths=["checkout -> payment_gateway", "payment_gateway -> provider_a"],
            authority_owner="governance",
            authority_basis="explicit_delegation",
        ),
        objective=AgentObjective(
            objective_id="obj_multi_001",
            description="Determine whether the system can safely process a payment.",
            target="payment_infrastructure",
            success_criteria=[
                "Identify all consequential dependencies",
                "Determine whether each dependency is governed",
                "Identify any authority escapes",
                "Propose appropriate remediation",
            ],
        ),
        available_sources=["checkout.py", "payment_gateway.py"],
        available_documentation=["DEPLOYMENT.md"],
        available_runtime_traces=["trace_001"],
        available_dependency_graph={
            "edges": [
                {"source": "checkout", "target": "payment_gateway"},
                {"source": "payment_gateway", "target": "provider_a"},
            ]
        },
        available_authority_graph={
            "edges": [
                {"source": "governance", "target": "payment_gateway", "type": "delegation"},
            ]
        },
        available_governance_policies={
            "policy_001": {"effect": "allow", "target": "provider_a"},
        },
    )

    # World State 1: Provider A → B (documentation drift)
    state_1 = WorldState(
        state_id=1,
        timestamp=now,
        infrastructure=PaymentInfrastructureState(
            timestamp=now,
            documented_provider="provider_a",
            actual_provider="provider_b",
            has_credential=True,
            credential_valid=True,
            delegation_active=True,
            delegation_expires="2027-01-01T00:00:00Z",
            policy_effect="allow",
            has_subprocess_path=False,
            has_legacy_processor=False,
            runtime_paths=["checkout -> payment_gateway", "payment_gateway -> provider_b"],
            authority_owner="governance",
            authority_basis="explicit_delegation",
        ),
        objective=AgentObjective(
            objective_id="obj_multi_002",
            description="Determine whether the system can safely process a payment after provider change.",
            target="payment_infrastructure",
            success_criteria=[
                "Identify provider change",
                "Determine if new provider is authorized",
                "Assess documentation drift",
            ],
        ),
        available_sources=["checkout.py", "payment_gateway.py"],
        available_documentation=["DEPLOYMENT.md"],  # Still says provider_a
        available_runtime_traces=["trace_001", "trace_002"],
        available_dependency_graph={
            "edges": [
                {"source": "checkout", "target": "payment_gateway"},
                {"source": "payment_gateway", "target": "provider_b"},
            ]
        },
        available_authority_graph={
            "edges": [
                {"source": "governance", "target": "payment_gateway", "type": "delegation"},
            ]
        },
        available_governance_policies={
            "policy_001": {"effect": "allow", "target": "provider_a"},
        },
        drift_findings=[
            {
                "drift_type": "documentation_drift",
                "description": "Documentation says provider_a, runtime uses provider_b",
            }
        ],
    )

    # World State 2: Delegation expires
    state_2 = WorldState(
        state_id=2,
        timestamp=now,
        infrastructure=PaymentInfrastructureState(
            timestamp=now,
            documented_provider="provider_a",
            actual_provider="provider_b",
            has_credential=True,
            credential_valid=True,
            delegation_active=False,
            delegation_expires="2026-01-01T00:00:00Z",  # EXPIRED
            policy_effect="allow",
            has_subprocess_path=False,
            has_legacy_processor=False,
            runtime_paths=["checkout -> payment_gateway", "payment_gateway -> provider_b"],
            authority_owner="governance",
            authority_basis="explicit_delegation",
        ),
        objective=AgentObjective(
            objective_id="obj_multi_003",
            description="Determine whether payment processing is still authorized after delegation expiration.",
            target="payment_infrastructure",
            success_criteria=[
                "Identify delegation expiration",
                "Determine if existing capabilities are still valid",
                "Assess authority staleness",
            ],
        ),
        available_sources=["checkout.py", "payment_gateway.py"],
        available_documentation=["DEPLOYMENT.md"],
        available_runtime_traces=["trace_001", "trace_002"],
        available_dependency_graph={
            "edges": [
                {"source": "checkout", "target": "payment_gateway"},
                {"source": "payment_gateway", "target": "provider_b"},
            ]
        },
        available_authority_graph={
            "edges": [
                {"source": "governance", "target": "payment_gateway", "type": "delegation"},
            ]
        },
        available_governance_policies={
            "policy_001": {"effect": "allow", "target": "provider_a"},
        },
        drift_findings=[
            {
                "drift_type": "staleness",
                "description": "Delegation expired",
            }
        ],
    )

    # World State 3: Policy prohibits provider_b
    state_3 = WorldState(
        state_id=3,
        timestamp=now,
        infrastructure=PaymentInfrastructureState(
            timestamp=now,
            documented_provider="provider_a",
            actual_provider="provider_b",
            has_credential=True,
            credential_valid=True,
            delegation_active=False,
            delegation_expires="2026-01-01T00:00:00Z",
            policy_effect="prohibit",  # Policy prohibits provider_b
            has_subprocess_path=True,
            has_legacy_processor=True,
            runtime_paths=[
                "checkout -> payment_gateway",
                "payment_gateway -> provider_b",
                "payment_gateway -> subprocess",
                "payment_gateway -> legacy_processor",
            ],
            authority_owner="ambiguous",
            authority_basis="explicit_delegation",
        ),
        objective=AgentObjective(
            objective_id="obj_multi_004",
            description="Determine remediation after policy change and authority ambiguity.",
            target="payment_infrastructure",
            success_criteria=[
                "Identify policy conflict",
                "Determine authority ambiguity",
                "Propose compliant remediation",
            ],
        ),
        available_sources=["checkout.py", "payment_gateway.py", "subprocess_handler.py", "legacy_processor.py"],
        available_documentation=["DEPLOYMENT.md", "ARCHITECTURE.md"],
        available_runtime_traces=["trace_001", "trace_002", "trace_003"],
        available_dependency_graph={
            "edges": [
                {"source": "checkout", "target": "payment_gateway"},
                {"source": "payment_gateway", "target": "provider_b"},
                {"source": "payment_gateway", "target": "subprocess"},
                {"source": "payment_gateway", "target": "legacy_processor"},
            ]
        },
        available_authority_graph={
            "edges": [
                {"source": "governance", "target": "payment_gateway", "type": "delegation"},
            ]
        },
        available_governance_policies={
            "policy_001": {"effect": "prohibit", "target": "provider_b"},
            "policy_002": {"effect": "allow", "target": "provider_a"},
        },
        drift_findings=[
            {
                "drift_type": "policy_conflict",
                "description": "Policy prohibits provider_b but runtime uses it",
            },
            {
                "drift_type": "authority_ambiguity",
                "description": "Authority owner is ambiguous",
            },
        ],
    )

    # World State 4: New delegation issued
    state_4 = WorldState(
        state_id=4,
        timestamp=now,
        infrastructure=PaymentInfrastructureState(
            timestamp=now,
            documented_provider="provider_a",
            actual_provider="provider_a",  # Reverted
            has_credential=True,
            credential_valid=True,
            delegation_active=True,
            delegation_expires="2028-01-01T00:00:00Z",  # New delegation
            policy_effect="allow",
            has_subprocess_path=True,
            has_legacy_processor=False,  # Removed
            runtime_paths=[
                "checkout -> payment_gateway",
                "payment_gateway -> provider_a",
                "payment_gateway -> subprocess",
            ],
            authority_owner="governance",
            authority_basis="explicit_delegation",
        ),
        objective=AgentObjective(
            objective_id="obj_multi_005",
            description="Verify system integrity after remediation.",
            target="payment_infrastructure",
            success_criteria=[
                "Verify provider is authorized",
                "Verify delegation is current",
                "Verify no authority escapes remain",
            ],
        ),
        available_sources=["checkout.py", "payment_gateway.py", "subprocess_handler.py"],
        available_documentation=["DEPLOYMENT.md", "ARCHITECTURE.md"],
        available_runtime_traces=["trace_001", "trace_004"],
        available_dependency_graph={
            "edges": [
                {"source": "checkout", "target": "payment_gateway"},
                {"source": "payment_gateway", "target": "provider_a"},
                {"source": "payment_gateway", "target": "subprocess"},
            ]
        },
        available_authority_graph={
            "edges": [
                {"source": "governance", "target": "payment_gateway", "type": "delegation"},
            ]
        },
        available_governance_policies={
            "policy_001": {"effect": "allow", "target": "provider_a"},
        },
    )

    events = [
        WorldEvent(
            event_id="event_init",
            timestamp=now,
            event_type=WorldEventType.PROVIDER_CHANGE,
            description="Initial state",
            pre_state=0,
            post_state=0,
            authority_impact="none",
        ),
        WorldEvent(
            event_id="event_provider_change",
            timestamp=now,
            event_type=WorldEventType.PROVIDER_CHANGE,
            description="Provider A → B",
            pre_state=0,
            post_state=1,
            authority_impact="authorization_mismatch",
            affected_resources=["provider_a", "provider_b"],
        ),
        WorldEvent(
            event_id="event_delegation_expire",
            timestamp=now,
            event_type=WorldEventType.DELEGATION_EXPIRE,
            description="Delegation expires",
            pre_state=1,
            post_state=2,
            authority_impact="authority_stale",
            affected_resources=["payment_gateway"],
        ),
        WorldEvent(
            event_id="event_policy_change",
            timestamp=now,
            event_type=WorldEventType.POLICY_CHANGE,
            description="Policy prohibits provider_b",
            pre_state=2,
            post_state=3,
            authority_impact="governance_conflict",
            affected_resources=["provider_b"],
        ),
        WorldEvent(
            event_id="event_remediation",
            timestamp=now,
            event_type=WorldEventType.REMEDIATION_APPLIED,
            description="Remediation applied: revert to provider_a, remove legacy",
            pre_state=3,
            post_state=4,
            authority_impact="authority_reconstructed",
            affected_resources=["provider_a", "legacy_processor"],
        ),
    ]

    return MultiAgentEnvironment(
        environment_id="env_multi_agent_001",
        current_state_id=0,
        world_states=[state_0, state_1, state_2, state_3, state_4],
        events=events,
        agent_ids=["researcher_001", "auditor_001", "operator_001"],
        shared_authority_state={
            "current_delegation": "delegation_001",
            "delegation_expires": "2027-01-01T00:00:00Z",
            "policy_effect": "allow",
            "authorized_providers": ["provider_a"],
        },
        shared_governance_state={
            "governance_owner": "governance",
            "last_policy_update": now,
            "active_policies": ["policy_001"],
        },
        shared_provenance=[],
    )
