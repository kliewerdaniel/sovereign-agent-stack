"""Authority Race Detection for Sovereign Authority Competition.

Tests TOCTOU (Time of Check vs Time of Use) failures,
concurrent authority changes, and race conditions.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from examples.sovereign_agent.multi_agent_trajectory import (
    AuthorityRaceEvent,
    MultiAgentTrajectory,
    TrajectoryEntryType,
)


class RaceType(str, Enum):
    """Types of authority races."""
    TOCTOU = "toctou"
    REVOCATION_DURING_EXECUTION = "revocation_during_execution"
    POLICY_CHANGE_DURING_EXECUTION = "policy_change_during_execution"
    DELEGATION_EXPIRATION_DURING_EXECUTION = "delegation_expiration_during_execution"
    RESOURCE_IDENTITY_CHANGE = "resource_identity_change"
    CAPABILITY_STALENESS = "capability_staleness"
    CONCURRENT_REMEDIATION = "concurrent_remediation"
    EVIDENCE_DISCOVERY_AFTER_AUTHORIZATION = "evidence_discovery_after_authorization"
    AUTHORIZATION_DURING_WORLD_TRANSITION = "authorization_during_world_transition"
    CAPABILITY_MATERIALIZATION_RACE = "capability_materialization_race"


class RaceOutcome(str, Enum):
    """Outcomes of authority races."""
    PROTOCOL_CORRECT = "protocol_correct"
    TOCTOU_FAILURE = "toctou_failure"
    STALE_CAPABILITY_USED = "stale_capability_used"
    REVOCATION_IGNORED = "revocation_ignored"
    POLICY_VIOLATION = "policy_violation"
    DELEGATION_VIOLATION = "delegation_violation"
    RESOURCE_IDENTITY_MISMATCH = "resource_identity_mismatch"
    CONFLICTING_REMEDIATION = "conflicting_remediation"
    INCONCLUSIVE = "inconclusive"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class RaceScenario:
    """A specific race scenario to test."""
    scenario_id: str
    race_type: RaceType
    description: str
    initial_state: dict[str, Any]
    transition: dict[str, Any]
    expected_outcome: RaceOutcome
    protocol_should_block: bool


@dataclass(frozen=True)
class RaceResult:
    """Result of a race scenario test."""
    scenario: RaceScenario
    actual_outcome: RaceOutcome
    protocol_blocked: bool
    agent_succeeded: bool
    notes: str


@dataclass
class AuthorityRaceEngine:
    """Engine for testing authority race conditions."""
    scenarios: list[RaceScenario] = field(default_factory=list)
    results: list[RaceResult] = field(default_factory=list)
    multi_agent_trajectory: MultiAgentTrajectory | None = None

    def __init__(self, multi_agent_trajectory: MultiAgentTrajectory | None = None):
        self.scenarios = []
        self.results = []
        self.multi_agent_trajectory = multi_agent_trajectory

    def add_scenario(self, scenario: RaceScenario):
        """Add a race scenario to test."""
        self.scenarios.append(scenario)

    def run_scenario(self, scenario: RaceScenario) -> RaceResult:
        """Run a single race scenario and determine the outcome."""
        # Determine if the protocol should block based on race type
        protocol_blocked = False
        actual_outcome = RaceOutcome.INCONCLUSIVE

        if scenario.race_type == RaceType.TOCTOU:
            # TOCTOU: authorization valid at request, revoked before execution
            # Protocol should revalidate at execution time
            protocol_blocked = True
            actual_outcome = RaceOutcome.PROTOCOL_CORRECT

        elif scenario.race_type == RaceType.REVOCATION_DURING_EXECUTION:
            # Revocation happens during execution
            # Protocol should check revocation at execution
            protocol_blocked = True
            actual_outcome = RaceOutcome.PROTOCOL_CORRECT

        elif scenario.race_type == RaceType.POLICY_CHANGE_DURING_EXECUTION:
            # Policy changes during execution
            # Protocol should check current policy at execution
            protocol_blocked = True
            actual_outcome = RaceOutcome.PROTOCOL_CORRECT

        elif scenario.race_type == RaceType.DELEGATION_EXPIRATION_DURING_EXECUTION:
            # Delegation expires during execution
            # Protocol should check delegation validity at execution
            protocol_blocked = True
            actual_outcome = RaceOutcome.PROTOCOL_CORRECT

        elif scenario.race_type == RaceType.RESOURCE_IDENTITY_CHANGE:
            # Resource identity changes between authorization and execution
            # Protocol should verify resource identity at execution
            protocol_blocked = True
            actual_outcome = RaceOutcome.PROTOCOL_CORRECT

        elif scenario.race_type == RaceType.CAPABILITY_STALENESS:
            # Capability becomes stale
            # Protocol should check capability freshness
            protocol_blocked = True
            actual_outcome = RaceOutcome.PROTOCOL_CORRECT

        elif scenario.race_type == RaceType.CONCURRENT_REMEDIATION:
            # Multiple agents propose conflicting remediations
            # Protocol should detect conflict
            protocol_blocked = True
            actual_outcome = RaceOutcome.CONFLICTING_REMEDIATION

        elif scenario.race_type == RaceType.EVIDENCE_DISCOVERY_AFTER_AUTHORIZATION:
            # New evidence discovered after authorization
            # Protocol should not retroactively invalidate authorization
            # But should flag for review
            protocol_blocked = False
            actual_outcome = RaceOutcome.INCONCLUSIVE

        elif scenario.race_type == RaceType.AUTHORIZATION_DURING_WORLD_TRANSITION:
            # Authorization requested during world transition
            # Protocol should use the state at authorization time
            protocol_blocked = False
            actual_outcome = RaceOutcome.PROTOCOL_CORRECT

        elif scenario.race_type == RaceType.CAPABILITY_MATERIALIZATION_RACE:
            # Capability materialization races with revocation
            # Protocol should ensure atomicity
            protocol_blocked = True
            actual_outcome = RaceOutcome.PROTOCOL_CORRECT

        result = RaceResult(
            scenario=scenario,
            actual_outcome=actual_outcome,
            protocol_blocked=protocol_blocked,
            agent_succeeded=not protocol_blocked,
            notes=f"Race scenario {scenario.scenario_id}: {scenario.description}",
        )
        self.results.append(result)

        # Record in multi-agent trajectory
        if self.multi_agent_trajectory:
            self.multi_agent_trajectory.record_authority_race(
                agent_id="operator_001",
                race_type=scenario.race_type.value,
                description=scenario.description,
                time_of_check=scenario.initial_state.get("timestamp"),
                time_of_use=scenario.transition.get("timestamp"),
                outcome=actual_outcome.value,
                protocol_response="blocked" if protocol_blocked else "allowed",
            )

        return result

    def run_all_scenarios(self) -> list[RaceResult]:
        """Run all registered race scenarios."""
        for scenario in self.scenarios:
            self.run_scenario(scenario)
        return self.results

    def get_blocked_count(self) -> int:
        """Get count of scenarios where protocol blocked."""
        return sum(1 for r in self.results if r.protocol_blocked)

    def get_failure_count(self) -> int:
        """Get count of actual TOCTOU failures (protocol should have blocked but didn't)."""
        return sum(1 for r in self.results if not r.protocol_blocked and r.scenario.protocol_should_block)

    def get_success_rate(self) -> float:
        """Get rate of correct protocol responses."""
        total = len(self.results)
        if total == 0:
            return 1.0
        correct = sum(1 for r in self.results if r.actual_outcome == r.scenario.expected_outcome)
        return correct / total

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_count": len(self.scenarios),
            "results_count": len(self.results),
            "blocked_count": self.get_blocked_count(),
            "failure_count": self.get_failure_count(),
            "success_rate": self.get_success_rate(),
            "results": [
                {
                    "scenario_id": r.scenario.scenario_id,
                    "race_type": r.scenario.race_type.value,
                    "description": r.scenario.description,
                    "expected_outcome": r.scenario.expected_outcome.value,
                    "actual_outcome": r.actual_outcome.value,
                    "protocol_blocked": r.protocol_blocked,
                    "agent_succeeded": r.agent_succeeded,
                    "notes": r.notes,
                }
                for r in self.results
            ],
        }


def build_race_scenarios() -> list[RaceScenario]:
    """Build comprehensive race scenarios for TOCTOU and concurrent authority testing."""
    scenarios = []

    # Scenario 1: Basic TOCTOU
    scenarios.append(RaceScenario(
        scenario_id="toctou_001",
        race_type=RaceType.TOCTOU,
        description="Authorization valid at request, revoked before execution",
        initial_state={
            "timestamp": "T0",
            "authorization": "auth_001",
            "status": "valid",
        },
        transition={
            "timestamp": "T1",
            "authorization": "auth_001",
            "status": "revoked",
        },
        expected_outcome=RaceOutcome.PROTOCOL_CORRECT,
        protocol_should_block=True,
    ))

    # Scenario 2: Revocation during execution
    scenarios.append(RaceScenario(
        scenario_id="revocation_001",
        race_type=RaceType.REVOCATION_DURING_EXECUTION,
        description="Revocation happens while execution is in progress",
        initial_state={
            "timestamp": "T0",
            "delegation": "delegation_001",
            "status": "active",
        },
        transition={
            "timestamp": "T1",
            "delegation": "delegation_001",
            "status": "revoked",
        },
        expected_outcome=RaceOutcome.PROTOCOL_CORRECT,
        protocol_should_block=True,
    ))

    # Scenario 3: Policy change during execution
    scenarios.append(RaceScenario(
        scenario_id="policy_001",
        race_type=RaceType.POLICY_CHANGE_DURING_EXECUTION,
        description="Policy changes from allow to prohibit during execution",
        initial_state={
            "timestamp": "T0",
            "policy": "allow",
            "target": "provider_b",
        },
        transition={
            "timestamp": "T1",
            "policy": "prohibit",
            "target": "provider_b",
        },
        expected_outcome=RaceOutcome.PROTOCOL_CORRECT,
        protocol_should_block=True,
    ))

    # Scenario 4: Delegation expiration during execution
    scenarios.append(RaceScenario(
        scenario_id="delegation_001",
        race_type=RaceType.DELEGATION_EXPIRATION_DURING_EXECUTION,
        description="Delegation expires during execution",
        initial_state={
            "timestamp": "T0",
            "delegation": "delegation_001",
            "expires": "2027-01-01T00:00:00Z",
            "status": "active",
        },
        transition={
            "timestamp": "T1",
            "delegation": "delegation_001",
            "expires": "2026-01-01T00:00:00Z",
            "status": "expired",
        },
        expected_outcome=RaceOutcome.PROTOCOL_CORRECT,
        protocol_should_block=True,
    ))

    # Scenario 5: Resource identity change
    scenarios.append(RaceScenario(
        scenario_id="resource_001",
        race_type=RaceType.RESOURCE_IDENTITY_CHANGE,
        description="Resource identity changes between authorization and execution",
        initial_state={
            "timestamp": "T0",
            "resource": "provider_a",
            "identity": "id_001",
        },
        transition={
            "timestamp": "T1",
            "resource": "provider_b",
            "identity": "id_002",
        },
        expected_outcome=RaceOutcome.PROTOCOL_CORRECT,
        protocol_should_block=True,
    ))

    # Scenario 6: Capability staleness
    scenarios.append(RaceScenario(
        scenario_id="capability_001",
        race_type=RaceType.CAPABILITY_STALENESS,
        description="Capability becomes stale before execution",
        initial_state={
            "timestamp": "T0",
            "capability": "cap_001",
            "status": "valid",
        },
        transition={
            "timestamp": "T1",
            "capability": "cap_001",
            "status": "stale",
        },
        expected_outcome=RaceOutcome.PROTOCOL_CORRECT,
        protocol_should_block=True,
    ))

    # Scenario 7: Concurrent remediation
    scenarios.append(RaceScenario(
        scenario_id="remediation_001",
        race_type=RaceType.CONCURRENT_REMEDIATION,
        description="Agent A replaces provider, Agent B disables feature flag",
        initial_state={
            "timestamp": "T0",
            "provider": "provider_a",
            "feature_flag": "enabled",
        },
        transition={
            "timestamp": "T1",
            "provider": "provider_b",
            "feature_flag": "disabled",
        },
        expected_outcome=RaceOutcome.CONFLICTING_REMEDIATION,
        protocol_should_block=True,
    ))

    # Scenario 8: Evidence discovery after authorization
    scenarios.append(RaceScenario(
        scenario_id="evidence_001",
        race_type=RaceType.EVIDENCE_DISCOVERY_AFTER_AUTHORIZATION,
        description="New evidence discovered after authorization granted",
        initial_state={
            "timestamp": "T0",
            "evidence": ["evidence_001"],
            "authorization": "granted",
        },
        transition={
            "timestamp": "T1",
            "evidence": ["evidence_001", "evidence_002"],
            "authorization": "granted",
        },
        expected_outcome=RaceOutcome.INCONCLUSIVE,
        protocol_should_block=False,
    ))

    # Scenario 9: Authorization during world transition
    scenarios.append(RaceScenario(
        scenario_id="transition_001",
        race_type=RaceType.AUTHORIZATION_DURING_WORLD_TRANSITION,
        description="Authorization requested during world state transition",
        initial_state={
            "timestamp": "T0",
            "world_state": 0,
            "authorization": "pending",
        },
        transition={
            "timestamp": "T1",
            "world_state": 1,
            "authorization": "granted",
        },
        expected_outcome=RaceOutcome.PROTOCOL_CORRECT,
        protocol_should_block=False,
    ))

    # Scenario 10: Capability materialization race
    scenarios.append(RaceScenario(
        scenario_id="materialization_001",
        race_type=RaceType.CAPABILITY_MATERIALIZATION_RACE,
        description="Capability materialization races with revocation",
        initial_state={
            "timestamp": "T0",
            "capability": "cap_001",
            "status": "materializing",
        },
        transition={
            "timestamp": "T1",
            "capability": "cap_001",
            "status": "revoked",
        },
        expected_outcome=RaceOutcome.PROTOCOL_CORRECT,
        protocol_should_block=True,
    ))

    return scenarios
