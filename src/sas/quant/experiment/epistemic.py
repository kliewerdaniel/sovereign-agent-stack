"""Observed Mechanism Artifact — what the agent actually found.

This is the crucial epistemic layer between "agent found something" and
"agent confirmed the hypothesis."

Key invariant:

    Performance is evidence of an outcome. It is not evidence of a cause.

A high Sharpe tells you that something happened. It does not tell you
what caused it. The ObservedMechanismArtifact records what was actually
observed, how it was measured, and what competing explanations exist.

Three distinct epistemic levels:

1. PREDICTABILITY: Is there evidence of exploitable structure?
2. MECHANISM: What observable explains the predictive relationship?
3. HYPOTHESIS: Does the identified mechanism satisfy the pre-registered hypothesis?
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Epistemic Status
# ---------------------------------------------------------------------------


class EpistemicStatus:
    """Epistemic status of a hypothesis given the evidence.

    Three-valued logic:
    - SUPPORTED: evidence confirms the hypothesis
    - REFUTED: evidence contradicts the hypothesis
    - INCONCLUSIVE: evidence neither confirms nor contradicts

    This is distinct from TRUE/FALSE because evidence can be ambiguous.
    """

    SUPPORTED = "supported"
    REFUTED = "refuted"
    INCONCLUSIVE = "inconclusive"


# ---------------------------------------------------------------------------
# Observed Mechanism Artifact
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ObservedMechanismArtifact:
    """Immutable record of the mechanism the agent actually discovered.

    This artifact captures what the agent found, how it was measured,
    and what competing explanations exist. It is the basis for comparing
    the observed mechanism against the declared hypothesis.

    Attributes:
        mechanism_id: Unique identifier.
        experiment_id: Parent experiment.
        trial_ids: Trials that contributed to this mechanism.
        mechanism_type: Type of mechanism (e.g., "momentum", "mean_reversion", "signal").
        features_used: Which features the strategy uses.
        information_horizon: How far ahead the mechanism predicts.
        dependency_measure: Statistical evidence (correlation, mutual information).
        evidence: List of evidence items supporting this mechanism.
        competing_mechanisms: Alternative explanations for the observed performance.
        confidence: Confidence in the mechanism identification (0-1).
        sharpe_ratio: Performance of the strategy using this mechanism.
        n_observations: Number of observations supporting this mechanism.
        n_trades: Number of trades in the strategy.
        created_at: Timestamp.
    """

    mechanism_id: str
    experiment_id: str
    trial_ids: list[str] = field(default_factory=list)
    mechanism_type: str = "unknown"
    features_used: list[str] = field(default_factory=list)
    information_horizon: str = "unknown"
    dependency_measure: float = 0.0
    evidence: list[str] = field(default_factory=list)
    competing_mechanisms: list[str] = field(default_factory=list)
    confidence: float = 0.0
    sharpe_ratio: float = 0.0
    n_observations: int = 0
    n_trades: int = 0
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "mechanism_id": self.mechanism_id,
            "experiment_id": self.experiment_id,
            "trial_ids": list(self.trial_ids),
            "mechanism_type": self.mechanism_type,
            "features_used": list(self.features_used),
            "information_horizon": self.information_horizon,
            "dependency_measure": self.dependency_measure,
            "evidence": list(self.evidence),
            "competing_mechanisms": list(self.competing_mechanisms),
            "confidence": self.confidence,
            "sharpe_ratio": self.sharpe_ratio,
            "n_observations": self.n_observations,
            "n_trades": self.n_trades,
            "created_at": self.created_at,
        }

    def is_statistically_significant(self, min_observations: int = 20) -> bool:
        """Check whether the mechanism has sufficient statistical support."""
        return (
            self.n_observations >= min_observations
            and self.n_trades >= 5
            and abs(self.dependency_measure) > 0.05
        )


# ---------------------------------------------------------------------------
# Epistemic Evaluation — compares observed mechanism against hypothesis
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EpistemicEvaluation:
    """Result of comparing an observed mechanism against a declared hypothesis.

    This is the core epistemic judgment: does the evidence support,
    refute, or fail to resolve the hypothesis?

    Attributes:
        hypothesis_id: The hypothesis being evaluated.
        mechanism_id: The observed mechanism being compared.
        status: SUPPORTED, REFUTED, or INCONCLUSIVE.
        reasoning: Human-readable reasoning.
        confidence: Confidence in the evaluation (0-1).
    """

    hypothesis_id: str
    mechanism_id: str
    status: str = EpistemicStatus.INCONCLUSIVE
    reasoning: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "hypothesis_id": self.hypothesis_id,
            "mechanism_id": self.mechanism_id,
            "status": self.status,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
        }


def evaluate_hypothesis(
    hypothesis: Any,
    mechanism: ObservedMechanismArtifact,
) -> EpistemicEvaluation:
    """Evaluate whether an observed mechanism supports a hypothesis.

    This is the core epistemic judgment. It compares the observed
    mechanism against the declared hypothesis and returns one of:
    - SUPPORTED: mechanism matches the hypothesis
    - REFUTED: mechanism contradicts the hypothesis
    - INCONCLUSIVE: evidence is ambiguous

    Key invariant:

        Agent performance alone NEVER establishes mechanism identity
        or hypothesis confirmation.

    Args:
        hypothesis: The declared hypothesis (HypothesisArtifact).
        mechanism: The observed mechanism (ObservedMechanismArtifact).

    Returns:
        EpistemicEvaluation with status and reasoning.
    """
    # Handle explicit "none" mechanism type first — agent says "I found nothing"
    # This bypasses statistical significance checks because it's a negative claim
    if mechanism.mechanism_type == "none":
        if hypothesis.target_signal == "none":
            # Agent found no predictability AND hypothesis says none exists → SUPPORTED
            return EpistemicEvaluation(
                hypothesis_id=hypothesis.hypothesis_id,
                mechanism_id=mechanism.mechanism_id,
                status=EpistemicStatus.SUPPORTED,
                reasoning=(
                    f"Null hypothesis supported: agent found no predictability. "
                    f"Agent Sharpe={mechanism.sharpe_ratio:.4f} (below threshold)."
                ),
                confidence=0.8,
            )
        else:
            # Agent found no predictability but signal hypothesis claims one exists
            # This does NOT refute the signal hypothesis (signal might exist but
            # agent failed to find it). It's INCONCLUSIVE.
            return EpistemicEvaluation(
                hypothesis_id=hypothesis.hypothesis_id,
                mechanism_id=mechanism.mechanism_id,
                status=EpistemicStatus.INCONCLUSIVE,
                reasoning=(
                    f"Signal hypothesis not supported: agent found no predictability. "
                    f"This does NOT refute the hypothesis — signal might exist but "
                    f"agent failed to find it. Sharpe={mechanism.sharpe_ratio:.4f}."
                ),
                confidence=0.2,
            )

    # Check for insufficient evidence (only for positive mechanism claims)
    if not mechanism.is_statistically_significant():
        return EpistemicEvaluation(
            hypothesis_id=hypothesis.hypothesis_id,
            mechanism_id=mechanism.mechanism_id,
            status=EpistemicStatus.INCONCLUSIVE,
            reasoning=(
                f"Insufficient evidence: {mechanism.n_observations} observations, "
                f"{mechanism.n_trades} trades, dependency={mechanism.dependency_measure:.4f}. "
                f"Need >= 20 observations, >= 5 trades, and |dependency| > 0.05."
            ),
            confidence=0.0,
        )

    # Check if mechanism matches hypothesis target
    if hypothesis.target_signal == "none":
        # Null hypothesis: no predictable pattern exists
        if mechanism.mechanism_type in hypothesis.confounders:
            return EpistemicEvaluation(
                hypothesis_id=hypothesis.hypothesis_id,
                mechanism_id=mechanism.mechanism_id,
                status=EpistemicStatus.REFUTED,
                reasoning=(
                    f"Null hypothesis refuted: agent found predictability from "
                    f"{mechanism.mechanism_type}, which is a known confounder. "
                    f"Sharpe={mechanism.sharpe_ratio:.4f}, "
                    f"dependency={mechanism.dependency_measure:.4f}."
                ),
                confidence=mechanism.confidence,
            )
        else:
            # Agent found some structure — null hypothesis in tension
            return EpistemicEvaluation(
                hypothesis_id=hypothesis.hypothesis_id,
                mechanism_id=mechanism.mechanism_id,
                status=EpistemicStatus.INCONCLUSIVE,
                reasoning=(
                    f"Null hypothesis ambiguous: agent found {mechanism.mechanism_type}, "
                    f"which is not a known confounder but not 'none'. "
                    f"Sharpe={mechanism.sharpe_ratio:.4f}."
                ),
                confidence=0.3,
            )
    else:
        # Signal hypothesis: specific signal exists
        if mechanism.mechanism_type == hypothesis.target_signal:
            return EpistemicEvaluation(
                hypothesis_id=hypothesis.hypothesis_id,
                mechanism_id=mechanism.mechanism_id,
                status=EpistemicStatus.SUPPORTED,
                reasoning=(
                    f"Hypothesis supported: agent found the declared signal "
                    f"({mechanism.mechanism_type}). "
                    f"Sharpe={mechanism.sharpe_ratio:.4f}, "
                    f"dependency={mechanism.dependency_measure:.4f}."
                ),
                confidence=mechanism.confidence,
            )
        elif mechanism.mechanism_type in hypothesis.confounders:
            return EpistemicEvaluation(
                hypothesis_id=hypothesis.hypothesis_id,
                mechanism_id=mechanism.mechanism_id,
                status=EpistemicStatus.REFUTED,
                reasoning=(
                    f"Hypothesis refuted: agent found predictability from "
                    f"{mechanism.mechanism_type}, not the declared signal "
                    f"({hypothesis.target_signal}). "
                    f"Sharpe={mechanism.sharpe_ratio:.4f} is from a confounder."
                ),
                confidence=mechanism.confidence,
            )
        else:
            return EpistemicEvaluation(
                hypothesis_id=hypothesis.hypothesis_id,
                mechanism_id=mechanism.mechanism_id,
                status=EpistemicStatus.INCONCLUSIVE,
                reasoning=(
                    f"Evidence inconclusive: agent found {mechanism.mechanism_type}, "
                    f"which is neither the declared signal nor a known confounder. "
                    f"Sharpe={mechanism.sharpe_ratio:.4f}."
                ),
                confidence=0.3,
            )
