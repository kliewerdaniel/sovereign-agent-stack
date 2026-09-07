"""Bounded reflection — the model's self-critique of its own strategy.

After backtest, the model gets ONE round (not unbounded) to critique
its own strategy and optionally propose a revision. The revision
becomes a completely new trial with a new provenance identity.

Reflection does NOT automatically mean revision. The model produces
a critique artifact that identifies potential weaknesses. It can then
either terminate the trial or produce a revised strategy.

The trial boundary is an execution boundary, not merely a reporting
convention. The model cannot perform unlimited optimization while the
system counts the entire process as one trial.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

from sas.quant.provenance.artifacts import CritiqueArtifact


@dataclass(frozen=True)
class ReflectionResult:
    """The result of a bounded reflection step."""

    critique: CritiqueArtifact
    should_revise: bool
    revised_strategy_spec: dict | None = None

    def to_dict(self) -> dict:
        return {
            "critique": self.critique.to_dict(),
            "should_revise": self.should_revise,
            "revised_strategy_spec": dict(self.revised_strategy_spec) if self.revised_strategy_spec else None,
        }


class BoundedReflector:
    """Manages bounded reflection for a single trial.

    One reflection round per trial. The model produces a critique
    artifact. If it chooses to revise, the revision becomes a new
    trial with parent_trial_id pointing to the original.
    """

    def __init__(self, max_reflection_rounds: int = 1):
        self.max_reflection_rounds = max_reflection_rounds

    def create_critique(
        self,
        trial_id: str,
        experiment_id: str,
        weaknesses: list[dict] | None = None,
        severity: str = "low",
        evidence: list[str] | None = None,
        recommendation: str = "terminate",
        action: str = "",
        reasoning: str = "",
        parent_trial_id: str | None = None,
    ) -> CritiqueArtifact:
        """Create a structured critique artifact."""
        return CritiqueArtifact(
            trial_id=trial_id,
            experiment_id=experiment_id,
            weaknesses=weaknesses or [],
            severity=severity,
            evidence=evidence or [],
            recommendation=recommendation,
            action=action,
            parent_trial_id=parent_trial_id,
            reasoning=reasoning,
        )

    def reflect(
        self,
        trial_id: str,
        experiment_id: str,
        critique: CritiqueArtifact,
        revised_strategy_spec: dict | None = None,
    ) -> ReflectionResult:
        """Process a reflection step.

        If the critique recommends revision and a revised strategy
        spec is provided, the revision becomes a new trial.
        """
        should_revise = critique.recommendation == "revise" and revised_strategy_spec is not None

        return ReflectionResult(
            critique=critique,
            should_revise=should_revise,
            revised_strategy_spec=revised_strategy_spec if should_revise else None,
        )

    def to_dict(self) -> dict:
        return {
            "max_reflection_rounds": self.max_reflection_rounds,
        }
