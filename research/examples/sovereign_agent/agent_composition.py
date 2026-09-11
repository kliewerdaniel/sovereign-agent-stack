"""Agent Composition for Sovereign Authority Competition.

Tests whether individually valid agent proposals compose into valid joint authority.
Implements the invariant: VALID(A) + VALID(B) + VALID(C) does NOT necessarily imply VALID(A+B+C)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from research.examples.sovereign_agent.intent_graph import ActionProposal


class CompositionType(str, Enum):
    """Types of agent compositions."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONFLICTING = "conflicting"
    COMPLEMENTARY = "complementary"
    REDUNDANT = "redundant"
    INTERDEPENDENT = "interdependent"


class CompositionStatus(str, Enum):
    """Status of a composition."""
    VALID = "valid"
    INVALID = "invalid"
    CONFLICTING = "conflicting"
    INCONCLUSIVE = "inconclusive"
    REQUIRES_GOVERNANCE = "requires_governance"


@dataclass(frozen=True)
class CompositionResult:
    """Result of composing multiple agent proposals."""
    composition_id: str
    timestamp: str
    proposals: list[ActionProposal]
    composition_type: CompositionType
    status: CompositionStatus
    individual_validity: dict[str, bool]
    joint_validity: bool
    conflict_details: list[str] = field(default_factory=list)
    resolution: Optional[str] = None


@dataclass
class AgentCompositionEngine:
    """Engine for testing agent proposal compositions."""
    compositions: list[CompositionResult] = field(default_factory=list)

    def compose_proposals(
        self,
        proposals: list[ActionProposal],
        composition_type: CompositionType,
    ) -> CompositionResult:
        """Compose multiple agent proposals and determine joint validity."""
        individual_validity = {}
        for proposal in proposals:
            individual_validity[proposal.agent_id] = self._check_individual_validity(proposal)

        joint_validity, conflict_details = self._check_joint_validity(proposals, composition_type)

        status = CompositionStatus.VALID if joint_validity else CompositionStatus.INVALID
        if conflict_details:
            status = CompositionStatus.CONFLICTING

        result = CompositionResult(
            composition_id=f"composition_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            proposals=proposals,
            composition_type=composition_type,
            status=status,
            individual_validity=individual_validity,
            joint_validity=joint_validity,
            conflict_details=conflict_details,
        )
        self.compositions.append(result)
        return result

    def _check_individual_validity(self, proposal: ActionProposal) -> bool:
        """Check if an individual proposal is valid."""
        # A proposal is individually valid if it has proper authorization
        if proposal.authorization_ref and not proposal.authorization_ref.startswith("stale_"):
            return True
        if proposal.capability_ref:
            return True
        return False

    def _check_joint_validity(
        self,
        proposals: list[ActionProposal],
        composition_type: CompositionType,
    ) -> tuple[bool, list[str]]:
        """Check if proposals are jointly valid."""
        conflicts = []

        if composition_type == CompositionType.CONFLICTING:
            # Conflicting proposals are never jointly valid
            conflicts.append("Proposals conflict: agents propose opposing actions")
            return False, conflicts

        if composition_type == CompositionType.INTERDEPENDENT:
            # Interdependent proposals require all to be valid
            for proposal in proposals:
                if not self._check_individual_validity(proposal):
                    conflicts.append(f"Interdependent proposal {proposal.proposal_id} is invalid")
                    return False, conflicts

        if composition_type == CompositionType.PARALLEL:
            # Parallel proposals must not affect the same resource
            resources = [p.resource for p in proposals]
            if len(resources) != len(set(resources)):
                conflicts.append("Parallel proposals affect the same resource")
                return False, conflicts

        if composition_type == CompositionType.SEQUENTIAL:
            # Sequential proposals must have proper ordering
            for i in range(len(proposals) - 1):
                if proposals[i].resource == proposals[i + 1].resource:
                    conflicts.append(f"Sequential proposals affect the same resource: {proposals[i].resource}")
                    return False, conflicts

        # Check for resource conflicts across all types
        resource_actions: dict[str, list[str]] = {}
        for proposal in proposals:
            if proposal.resource not in resource_actions:
                resource_actions[proposal.resource] = []
            resource_actions[proposal.resource].append(proposal.action)

        for resource, actions in resource_actions.items():
            if len(actions) > 1:
                # Multiple actions on same resource - check for conflicts
                if "replace" in actions and "disable" in actions:
                    conflicts.append(f"Conflict on {resource}: replace vs disable")
                    return False, conflicts
                if "replace" in actions and "remove" in actions:
                    conflicts.append(f"Conflict on {resource}: replace vs remove")
                    return False, conflicts

        return len(conflicts) == 0, conflicts

    def get_valid_compositions(self) -> list[CompositionResult]:
        """Get all valid compositions."""
        return [c for c in self.compositions if c.status == CompositionStatus.VALID]

    def get_invalid_compositions(self) -> list[CompositionResult]:
        """Get all invalid compositions."""
        return [c for c in self.compositions if c.status == CompositionStatus.INVALID]

    def get_conflicting_compositions(self) -> list[CompositionResult]:
        """Get all conflicting compositions."""
        return [c for c in self.compositions if c.status == CompositionStatus.CONFLICTING]

    def get_composition_failure_rate(self) -> float:
        """Get rate of composition failures."""
        total = len(self.compositions)
        if total == 0:
            return 0.0
        failures = sum(1 for c in self.compositions if not c.joint_validity)
        return failures / total

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "composition_count": len(self.compositions),
            "valid_count": len(self.get_valid_compositions()),
            "invalid_count": len(self.get_invalid_compositions()),
            "conflicting_count": len(self.get_conflicting_compositions()),
            "failure_rate": self.get_composition_failure_rate(),
            "compositions": [
                {
                    "composition_id": c.composition_id,
                    "composition_type": c.composition_type.value,
                    "status": c.status.value,
                    "proposal_count": len(c.proposals),
                    "individual_validity": c.individual_validity,
                    "joint_validity": c.joint_validity,
                    "conflict_details": c.conflict_details,
                }
                for c in self.compositions
            ],
        }


def build_composition_scenarios(
    engine: AgentCompositionEngine,
    researcher_id: str,
    auditor_id: str,
    operator_id: str,
) -> list[CompositionResult]:
    """Build composition scenarios for testing."""
    results = []

    # Scenario 1: Complementary proposals (A + B)
    p1 = ActionProposal(
        proposal_id="prop_001",
        agent_id=researcher_id,
        timestamp=datetime.utcnow().isoformat(),
        action="replace",
        resource="provider",
        arguments={"new_provider": "provider_a"},
        proposition="Replace provider with provider_a",
        authorization_ref="auth_001",
    )
    p2 = ActionProposal(
        proposal_id="prop_002",
        agent_id=auditor_id,
        timestamp=datetime.utcnow().isoformat(),
        action="disable",
        resource="feature_flag",
        arguments={"flag": "legacy_mode"},
        proposition="Disable legacy mode feature flag",
        authorization_ref="auth_002",
    )
    result1 = engine.compose_proposals([p1, p2], CompositionType.COMPLEMENTARY)
    results.append(result1)

    # Scenario 2: Conflicting proposals (A + C)
    p3 = ActionProposal(
        proposal_id="prop_003",
        agent_id=researcher_id,
        timestamp=datetime.utcnow().isoformat(),
        action="replace",
        resource="provider",
        arguments={"new_provider": "provider_b"},
        proposition="Replace provider with provider_b",
        authorization_ref="auth_003",
    )
    p4 = ActionProposal(
        proposal_id="prop_004",
        agent_id=operator_id,
        timestamp=datetime.utcnow().isoformat(),
        action="disable",
        resource="provider",
        arguments={},
        proposition="Disable provider",
        authorization_ref="auth_004",
    )
    result2 = engine.compose_proposals([p3, p4], CompositionType.CONFLICTING)
    results.append(result2)

    # Scenario 3: Triple composition (A + B + C)
    p5 = ActionProposal(
        proposal_id="prop_005",
        agent_id=researcher_id,
        timestamp=datetime.utcnow().isoformat(),
        action="replace",
        resource="provider",
        arguments={"new_provider": "provider_a"},
        proposition="Replace provider with provider_a",
        authorization_ref="auth_005",
    )
    p6 = ActionProposal(
        proposal_id="prop_006",
        agent_id=auditor_id,
        timestamp=datetime.utcnow().isoformat(),
        action="disable",
        resource="feature_flag",
        arguments={"flag": "legacy_mode"},
        proposition="Disable legacy mode feature flag",
        authorization_ref="auth_006",
    )
    p7 = ActionProposal(
        proposal_id="prop_007",
        agent_id=operator_id,
        timestamp=datetime.utcnow().isoformat(),
        action="remove",
        resource="legacy_processor",
        arguments={},
        proposition="Remove legacy processor",
        authorization_ref="auth_007",
    )
    result3 = engine.compose_proposals([p5, p6, p7], CompositionType.COMPLEMENTARY)
    results.append(result3)

    # Scenario 4: Parallel proposals on different resources
    p8 = ActionProposal(
        proposal_id="prop_008",
        agent_id=researcher_id,
        timestamp=datetime.utcnow().isoformat(),
        action="replace",
        resource="provider",
        arguments={"new_provider": "provider_a"},
        proposition="Replace provider with provider_a",
        authorization_ref="auth_008",
    )
    p9 = ActionProposal(
        proposal_id="prop_009",
        agent_id=auditor_id,
        timestamp=datetime.utcnow().isoformat(),
        action="remove",
        resource="legacy_processor",
        arguments={},
        proposition="Remove legacy processor",
        authorization_ref="auth_009",
    )
    result4 = engine.compose_proposals([p8, p9], CompositionType.PARALLEL)
    results.append(result4)

    # Scenario 5: Sequential proposals on same resource
    p10 = ActionProposal(
        proposal_id="prop_010",
        agent_id=researcher_id,
        timestamp=datetime.utcnow().isoformat(),
        action="replace",
        resource="provider",
        arguments={"new_provider": "provider_b"},
        proposition="Replace provider with provider_b",
        authorization_ref="auth_010",
    )
    p11 = ActionProposal(
        proposal_id="prop_011",
        agent_id=operator_id,
        timestamp=datetime.utcnow().isoformat(),
        action="disable",
        resource="provider",
        arguments={},
        proposition="Disable provider",
        authorization_ref="auth_011",
    )
    result5 = engine.compose_proposals([p10, p11], CompositionType.SEQUENTIAL)
    results.append(result5)

    return results
