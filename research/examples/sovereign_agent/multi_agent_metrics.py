"""Multi-Agent Metrics for Sovereign Authority Competition.

Tracks metrics across multiple autonomous agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MultiAgentMetrics:
    """Metrics for the multi-agent authority competition."""
    # Agent counts
    agent_count: int = 0
    researcher_count: int = 0
    auditor_count: int = 0
    operator_count: int = 0
    governance_count: int = 0

    # Trajectory metrics
    total_trajectory_length: int = 0
    trajectory_lengths: dict[str, int] = field(default_factory=dict)

    # Evidence metrics
    independent_evidence_count: int = 0
    dependent_evidence_count: int = 0
    evidence_independence_rate: float = 1.0

    # Disagreement metrics
    agreement_events: int = 0
    disagreement_events: int = 0
    resolved_disagreements: int = 0
    unresolved_disagreements: int = 0
    disagreement_resolution_rate: float = 1.0

    # Authority laundering metrics
    authority_laundering_attempts: int = 0
    authority_laundering_prevented: int = 0
    authority_laundering_prevention_rate: float = 1.0

    # TOCTOU metrics
    toctou_attempts: int = 0
    toctou_prevented: int = 0
    toctou_prevention_rate: float = 1.0

    # Revocation metrics
    stale_capability_attempts: int = 0
    revoked_authority_attempts: int = 0
    revocation_detection_rate: float = 1.0

    # Consequence metrics
    unauthorized_consequences: int = 0
    legitimate_consequences: int = 0
    false_refusals: int = 0
    successful_remediations: int = 0
    conflicting_remediations: int = 0

    # Composition metrics
    composition_failures: int = 0
    composition_successes: int = 0
    composition_failure_rate: float = 0.0

    # Recovery metrics
    historical_reconstruction_success: bool = True
    provenance_completeness: float = 1.0

    # Protocol metrics
    protocol_escapes: int = 0
    protocol_compliance_rate: float = 1.0

    # Authority-preserving autonomy
    authority_preserving_autonomy: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_count": self.agent_count,
            "researcher_count": self.researcher_count,
            "auditor_count": self.auditor_count,
            "operator_count": self.operator_count,
            "governance_count": self.governance_count,
            "total_trajectory_length": self.total_trajectory_length,
            "trajectory_lengths": self.trajectory_lengths,
            "independent_evidence_count": self.independent_evidence_count,
            "dependent_evidence_count": self.dependent_evidence_count,
            "evidence_independence_rate": self.evidence_independence_rate,
            "agreement_events": self.agreement_events,
            "disagreement_events": self.disagreement_events,
            "resolved_disagreements": self.resolved_disagreements,
            "unresolved_disagreements": self.unresolved_disagreements,
            "disagreement_resolution_rate": self.disagreement_resolution_rate,
            "authority_laundering_attempts": self.authority_laundering_attempts,
            "authority_laundering_prevented": self.authority_laundering_prevented,
            "authority_laundering_prevention_rate": self.authority_laundering_prevention_rate,
            "toctou_attempts": self.toctou_attempts,
            "toctou_prevented": self.toctou_prevented,
            "toctou_prevention_rate": self.toctou_prevention_rate,
            "stale_capability_attempts": self.stale_capability_attempts,
            "revoked_authority_attempts": self.revoked_authority_attempts,
            "revocation_detection_rate": self.revocation_detection_rate,
            "unauthorized_consequences": self.unauthorized_consequences,
            "legitimate_consequences": self.legitimate_consequences,
            "false_refusals": self.false_refusals,
            "successful_remediations": self.successful_remediations,
            "conflicting_remediations": self.conflicting_remediations,
            "composition_failures": self.composition_failures,
            "composition_successes": self.composition_successes,
            "composition_failure_rate": self.composition_failure_rate,
            "historical_reconstruction_success": self.historical_reconstruction_success,
            "provenance_completeness": self.provenance_completeness,
            "protocol_escapes": self.protocol_escapes,
            "protocol_compliance_rate": self.protocol_compliance_rate,
            "authority_preserving_autonomy": self.authority_preserving_autonomy,
        }
