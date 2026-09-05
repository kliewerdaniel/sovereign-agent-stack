"""Quant lifecycle state machine.

Research lifecycle:
  DATA → DATASET → HYPOTHESIS → SIGNAL → STRATEGY → BACKTEST
  → EVALUATION → RISK_REVIEW → APPROVAL → PORTFOLIO
  → RESEARCH_REPORT → MONITORING → POST_ANALYSIS

Every transition is an artifact. Nothing exists only in conversational context.
"""
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from typing import Optional


class ResearchStage(enum.Enum):
    DATA = "data"
    DATASET = "dataset"
    HYPOTHESIS = "hypothesis"
    SIGNAL = "signal"
    STRATEGY = "strategy"
    BACKTEST = "backtest"
    EVALUATION = "evaluation"
    RISK_REVIEW = "risk_review"
    APPROVAL = "approval"
    PORTFOLIO = "portfolio"
    RESEARCH_REPORT = "research_report"
    MONITORING = "monitoring"
    POST_ANALYSIS = "post_analysis"

    @property
    def is_terminal(self) -> bool:
        return self in (self.POST_ANALYSIS,)


# Valid transitions
TRANSITIONS = {
    ResearchStage.DATA: {ResearchStage.DATASET},
    ResearchStage.DATASET: {ResearchStage.HYPOTHESIS},
    ResearchStage.HYPOTHESIS: {ResearchStage.SIGNAL},
    ResearchStage.SIGNAL: {ResearchStage.STRATEGY},
    ResearchStage.STRATEGY: {ResearchStage.BACKTEST},
    ResearchStage.BACKTEST: {ResearchStage.EVALUATION},
    ResearchStage.EVALUATION: {ResearchStage.RISK_REVIEW},
    ResearchStage.RISK_REVIEW: {ResearchStage.APPROVAL},
    ResearchStage.APPROVAL: {ResearchStage.PORTFOLIO},
    ResearchStage.PORTFOLIO: {ResearchStage.RESEARCH_REPORT},
    ResearchStage.RESEARCH_REPORT: {ResearchStage.MONITORING},
    ResearchStage.MONITORING: {ResearchStage.POST_ANALYSIS},
    ResearchStage.POST_ANALYSIS: set(),
}


@dataclass
class LifecycleTransition:
    """A single lifecycle transition — an artifact."""
    transition_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    from_stage: str = ""
    to_stage: str = ""
    artifact_id: str = ""
    actor: str = "unknown"
    reason: str = ""
    timestamp: str = field(default_factory=lambda: __import__('datetime',
        fromlist=['datetime']).datetime.now(__import__('datetime',
        fromlist=['timezone'], level=0).timezone.utc).isoformat())
    provenance: dict = field(default_factory=dict)


@dataclass
class ResearchLifecycle:
    """Tracks a research item through its lifecycle."""
    lifecycle_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    artifact_id: str = ""
    current_stage: ResearchStage = ResearchStage.DATA
    transitions: list[LifecycleTransition] = field(default_factory=list)
    artifacts: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: __import__('datetime',
        fromlist=['datetime']).datetime.now(__import__('datetime',
        fromlist=['timezone'], level=0).timezone.utc).isoformat())

    def transition_to(self, to_stage: ResearchStage,
                       actor: str = "unknown",
                       reason: str = "") -> LifecycleTransition:
        """Transition to a new stage."""
        valid = TRANSITIONS.get(self.current_stage, set())
        if to_stage not in valid and not self.current_stage.is_terminal:
            raise ValueError(
                f"Invalid transition: {self.current_stage.value} -> {to_stage.value}"
            )

        t = LifecycleTransition(
            from_stage=self.current_stage.value,
            to_stage=to_stage.value,
            artifact_id=self.artifact_id,
            actor=actor,
            reason=reason,
        )
        self.transitions.append(t)
        self.current_stage = to_stage
        return t

    def is_complete(self) -> bool:
        return self.current_stage == ResearchStage.POST_ANALYSIS

    def to_dict(self) -> dict:
        return {
            "lifecycle_id": self.lifecycle_id,
            "artifact_id": self.artifact_id,
            "current_stage": self.current_stage.value,
            "transitions": [
                {
                    "id": t.transition_id,
                    "from": t.from_stage,
                    "to": t.to_stage,
                    "actor": t.actor,
                    "reason": t.reason,
                    "timestamp": t.timestamp,
                }
                for t in self.transitions
            ],
            "artifacts": self.artifacts,
            "created_at": self.created_at,
        }