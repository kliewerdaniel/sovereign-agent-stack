"""Agent Disagreement Engine for Sovereign Authority Competition.

Handles deliberate disagreements between agents.
Ensures disagreement is represented as disagreement,
not resolved through confidence, recency, role, or majority.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from examples.sovereign_agent.multi_agent_trajectory import (
    AgentTrajectory,
    DisagreementEvent,
    MultiAgentTrajectory,
    TrajectoryEntryType,
)


class DisagreementType(str, Enum):
    """Types of agent disagreements."""
    DEPENDENCY_CRITICALITY = "dependency_criticality"
    PROVIDER_STATUS = "provider_status"
    AUTHORIZATION_VALIDITY = "authorization_validity"
    EVIDENCE_INTERPRETATION = "evidence_interpretation"
    TEMPORAL_SCOPE = "temporal_scope"
    REMEDIATION_PRIORITY = "remediation_priority"
    AUTHORITY_SCOPE = "authority_scope"
    PROVENANCE_COMPLETENESS = "provenance_completeness"
    RISK_ASSESSMENT = "risk_assessment"
    DELEGATION_STATUS = "delegation_status"


class ResolutionMechanism(str, Enum):
    """Mechanisms for resolving disagreements."""
    EVIDENCE_ACCUMULATION = "evidence_accumulation"
    GOVERNANCE_REVIEW = "governance_review"
    TEMPORAL_VERIFICATION = "temporal_verification"
    PROVENANCE_RECONSTRUCTION = "provenance_reconstruction"
    EXPERIMENT_DISCRIMINATION = "experiment_discrimination"
    EXTERNAL_ADJUDICATION = "external_adjudication"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class AgentPosition:
    """A position taken by an agent on a proposition."""
    agent_id: str
    timestamp: str
    proposition: str
    position: str
    confidence: float
    evidence: list[str]
    reasoning: str
    authority_basis: Optional[str] = None


@dataclass(frozen=True)
class DisagreementRecord:
    """Full record of a disagreement between agents."""
    record_id: str
    timestamp: str
    disagreement_type: DisagreementType
    proposition: str
    positions: list[AgentPosition]
    evidence_overlap: list[str]
    evidence_independent: list[str]
    contradictions: list[str]
    resolution: Optional[str] = None
    resolution_mechanism: Optional[ResolutionMechanism] = None
    resolution_timestamp: Optional[str] = None
    protocol_compliant: bool = True


@dataclass
class AgentDisagreementEngine:
    """Engine for managing agent disagreements."""
    disagreements: list[DisagreementRecord] = field(default_factory=list)
    multi_agent_trajectory: MultiAgentTrajectory | None = None

    def __init__(self, multi_agent_trajectory: MultiAgentTrajectory | None = None):
        self.disagreements = []
        self.multi_agent_trajectory = multi_agent_trajectory

    def record_disagreement(
        self,
        disagreement_type: DisagreementType,
        proposition: str,
        positions: list[AgentPosition],
        evidence_overlap: list[str] | None = None,
        evidence_independent: list[str] | None = None,
        contradictions: list[str] | None = None,
    ) -> DisagreementRecord:
        """Record a disagreement between agents."""
        record = DisagreementRecord(
            record_id=f"disagree_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            disagreement_type=disagreement_type,
            proposition=proposition,
            positions=positions,
            evidence_overlap=evidence_overlap or [],
            evidence_independent=evidence_independent or [],
            contradictions=contradictions or [],
        )
        self.disagreements.append(record)

        # Also record in multi-agent trajectory if available
        if self.multi_agent_trajectory and len(positions) >= 2:
            self.multi_agent_trajectory.record_disagreement(
                agent_a_id=positions[0].agent_id,
                agent_b_id=positions[1].agent_id,
                proposition=proposition,
                agent_a_position=positions[0].position,
                agent_b_position=positions[1].position,
                evidence_overlap=evidence_overlap,
                evidence_independent=evidence_independent,
            )

        return record

    def resolve_disagreement(
        self,
        record_id: str,
        resolution: str,
        mechanism: ResolutionMechanism,
    ) -> Optional[DisagreementRecord]:
        """Resolve a disagreement through protocol-compliant mechanisms."""
        for i, record in enumerate(self.disagreements):
            if record.record_id == record_id:
                resolved = DisagreementRecord(
                    record_id=record.record_id,
                    timestamp=record.timestamp,
                    disagreement_type=record.disagreement_type,
                    proposition=record.proposition,
                    positions=record.positions,
                    evidence_overlap=record.evidence_overlap,
                    evidence_independent=record.evidence_independent,
                    contradictions=record.contradictions,
                    resolution=resolution,
                    resolution_mechanism=mechanism,
                    resolution_timestamp=datetime.utcnow().isoformat(),
                )
                self.disagreements[i] = resolved

                # Update multi-agent trajectory if available
                if self.multi_agent_trajectory:
                    for event in self.multi_agent_trajectory.disagreement_events:
                        if event.agent_a_id == record.positions[0].agent_id and event.agent_b_id == record.positions[1].agent_id and event.proposition == record.proposition:
                            event.resolution = resolution
                            event.resolution_mechanism = mechanism.value

                return resolved
        return None

    def check_authority_laundering(
        self,
        agent_a_id: str,
        agent_b_id: str,
        action: str,
    ) -> dict[str, Any]:
        """Check if an action constitutes authority laundering between agents."""
        # Check if one agent is using another's output as authority
        laundering_checks = {
            "agent_a_authorizes_agent_b": False,
            "agent_b_authorizes_agent_a": False,
            "agent_a_confidence_as_authority": False,
            "agent_b_confidence_as_authority": False,
            "mutual_agreement_as_authority": False,
            "role_as_authority": False,
            "proximity_as_authority": False,
        }

        # Check trajectory entries for authority laundering patterns
        if self.multi_agent_trajectory:
            traj_a = self.multi_agent_trajectory.trajectories.get(agent_a_id)
            traj_b = self.multi_agent_trajectory.trajectories.get(agent_b_id)

            if traj_a and traj_b:
                # Check if Agent A uses Agent B's output as authority
                for entry in traj_a.entries:
                    if entry.entry_type == TrajectoryEntryType.AUTHORIZATION_REQUEST:
                        if agent_b_id in str(entry.content):
                            laundering_checks["agent_a_authorizes_agent_b"] = True

                # Check if Agent B uses Agent A's output as authority
                for entry in traj_b.entries:
                    if entry.entry_type == TrajectoryEntryType.AUTHORIZATION_REQUEST:
                        if agent_a_id in str(entry.content):
                            laundering_checks["agent_b_authorizes_agent_a"] = True

        return {
            "is_laundering": any(laundering_checks.values()),
            "checks": laundering_checks,
            "action": action,
            "agent_a_id": agent_a_id,
            "agent_b_id": agent_b_id,
        }

    def get_independent_evidence_count(self) -> int:
        """Get count of disagreements with independent evidence."""
        return sum(1 for d in self.disagreements if d.evidence_independent)

    def get_dependent_evidence_count(self) -> int:
        """Get count of disagreements with only dependent/redundant evidence."""
        return sum(1 for d in self.disagreements if not d.evidence_independent)

    def get_unresolved_count(self) -> int:
        """Get number of unresolved disagreements."""
        return sum(1 for d in self.disagreements if d.resolution is None)

    def get_resolution_rate(self) -> float:
        """Get rate of resolved disagreements."""
        total = len(self.disagreements)
        if total == 0:
            return 1.0
        resolved = sum(1 for d in self.disagreements if d.resolution is not None)
        return resolved / total

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "disagreement_count": len(self.disagreements),
            "resolved_count": sum(1 for d in self.disagreements if d.resolution is not None),
            "unresolved_count": self.get_unresolved_count(),
            "resolution_rate": self.get_resolution_rate(),
            "independent_evidence_count": self.get_independent_evidence_count(),
            "dependent_evidence_count": self.get_dependent_evidence_count(),
            "disagreements": [
                {
                    "record_id": d.record_id,
                    "timestamp": d.timestamp,
                    "disagreement_type": d.disagreement_type.value,
                    "proposition": d.proposition,
                    "positions": [
                        {
                            "agent_id": p.agent_id,
                            "position": p.position,
                            "confidence": p.confidence,
                            "evidence": p.evidence,
                            "reasoning": p.reasoning,
                        }
                        for p in d.positions
                    ],
                    "evidence_overlap": d.evidence_overlap,
                    "evidence_independent": d.evidence_independent,
                    "resolution": d.resolution,
                    "resolution_mechanism": d.resolution_mechanism.value if d.resolution_mechanism else None,
                }
                for d in self.disagreements
            ],
        }


def build_deliberate_disagreements(
    engine: AgentDisagreementEngine,
    researcher_trajectory: AgentTrajectory,
    auditor_trajectory: AgentTrajectory,
    operator_trajectory: AgentTrajectory,
) -> list[DisagreementRecord]:
    """Build deliberate disagreement scenarios."""
    disagreements = []

    # Disagreement 1: Dependency criticality
    pos1 = AgentPosition(
        agent_id=researcher_trajectory.agent_id,
        timestamp=datetime.utcnow().isoformat(),
        proposition="Dependency X is operationally required",
        position="required",
        confidence=0.85,
        evidence=["runtime_traces", "static_analysis"],
        reasoning="Runtime traces show active usage",
    )
    pos2 = AgentPosition(
        agent_id=auditor_trajectory.agent_id,
        timestamp=datetime.utcnow().isoformat(),
        proposition="Dependency X is operationally required",
        position="optional",
        confidence=0.75,
        evidence=["documentation", "configuration"],
        reasoning="Documentation lists it as optional",
    )
    d1 = engine.record_disagreement(
        disagreement_type=DisagreementType.DEPENDENCY_CRITICALITY,
        proposition="Dependency X is operationally required",
        positions=[pos1, pos2],
        evidence_overlap=["runtime_traces"],
        evidence_independent=["documentation", "configuration", "static_analysis"],
        contradictions=["required vs optional"],
    )
    disagreements.append(d1)

    # Disagreement 2: Provider status
    pos3 = AgentPosition(
        agent_id=researcher_trajectory.agent_id,
        timestamp=datetime.utcnow().isoformat(),
        proposition="Provider B is the active provider",
        position="active",
        confidence=0.90,
        evidence=["runtime_traces"],
        reasoning="Runtime shows provider_b in use",
    )
    pos4 = AgentPosition(
        agent_id=auditor_trajectory.agent_id,
        timestamp=datetime.utcnow().isoformat(),
        proposition="Provider B is the active provider",
        position="configured_not_active",
        confidence=0.80,
        evidence=["configuration"],
        reasoning="Provider B is configured but not runtime-active",
    )
    d2 = engine.record_disagreement(
        disagreement_type=DisagreementType.PROVIDER_STATUS,
        proposition="Provider B is the active provider",
        positions=[pos3, pos4],
        evidence_overlap=[],
        evidence_independent=["runtime_traces", "configuration"],
        contradictions=["active vs configured_not_active"],
    )
    disagreements.append(d2)

    # Disagreement 3: Authorization validity
    pos5 = AgentPosition(
        agent_id=operator_trajectory.agent_id,
        timestamp=datetime.utcnow().isoformat(),
        proposition="Existing authorization permits remediation",
        position="valid",
        confidence=0.70,
        evidence=["authorization_record"],
        reasoning="Authorization was issued and not revoked",
    )
    pos6 = AgentPosition(
        agent_id=auditor_trajectory.agent_id,
        timestamp=datetime.utcnow().isoformat(),
        proposition="Existing authorization permits remediation",
        position="stale",
        confidence=0.85,
        evidence=["temporal_snapshot", "revocation_log"],
        reasoning="Authorization is stale due to delegation expiration",
    )
    d3 = engine.record_disagreement(
        disagreement_type=DisagreementType.AUTHORIZATION_VALIDITY,
        proposition="Existing authorization permits remediation",
        positions=[pos5, pos6],
        evidence_overlap=["authorization_record"],
        evidence_independent=["temporal_snapshot", "revocation_log"],
        contradictions=["valid vs stale"],
    )
    disagreements.append(d3)

    # Disagreement 4: Temporal scope
    pos7 = AgentPosition(
        agent_id=researcher_trajectory.agent_id,
        timestamp=datetime.utcnow().isoformat(),
        proposition="Historical evidence supports this action",
        position="supports",
        confidence=0.75,
        evidence=["historical_snapshot"],
        reasoning="Historical state shows the action was previously authorized",
    )
    pos8 = AgentPosition(
        agent_id=auditor_trajectory.agent_id,
        timestamp=datetime.utcnow().isoformat(),
        proposition="Historical evidence supports this action",
        position="not_current_authority",
        confidence=0.90,
        evidence=["current_state", "temporal_rules"],
        reasoning="Historical evidence does not establish current authority",
    )
    d4 = engine.record_disagreement(
        disagreement_type=DisagreementType.TEMPORAL_SCOPE,
        proposition="Historical evidence supports this action",
        positions=[pos7, pos8],
        evidence_overlap=["historical_snapshot"],
        evidence_independent=["current_state", "temporal_rules"],
        contradictions=["supports vs not_current_authority"],
    )
    disagreements.append(d4)

    return disagreements
