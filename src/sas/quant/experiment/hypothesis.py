"""Hypothesis Artifact — provenance for the researcher's declared hypothesis.

The critical distinction this enables:

    DGP contains predictability
        ≠
    DGP contains the predictability hypothesized by the researcher

A strategy that profits from an unintended confounder must NOT be
considered confirmation of the declared hypothesis merely because its
Sharpe is high.

Example:

    Hypothesis: future return depends on X
    Observed:   future return is predictable from autocorrelation
    Conclusion: hypothesis NOT established (even if strategy profits)

This artifact captures what the experiment CLAIMS to be testing, so that
results can be attributed to the correct epistemic category.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class HypothesisArtifact:
    """Immutable record of the researcher's declared hypothesis.

    This artifact describes what the experiment claims to be testing.
    It is the reference against which observed predictability is compared.

    The hypothesis is NOT the DGP (which describes the world). The hypothesis
    is the claim about what pattern the researcher expects to find in the world.

    Key distinction:
        - DGP: "The world has autocorrelation=0.3 and signal_strength=0.0"
        - Hypothesis: "The researcher claims no predictable pattern exists"

    If the agent finds a profitable strategy in a Null AR world, the hypothesis
    ("no predictable pattern") is FALSE — even though the DGP is exactly as declared.

    Attributes:
        hypothesis_id: Unique identifier.
        experiment_id: Parent experiment.
        claim: Human-readable statement of the hypothesis.
        target_signal: The specific signal being tested (e.g., "momentum at lag 1").
        allowed_observables: Which data features the agent may use.
        expected_direction: "positive", "negative", "state_dependent", "none".
        expected_effect: Expected magnitude (e.g., Sharpe contribution).
        information_horizon: How far ahead the signal predicts ("t+1", "t+5").
        confounders: Known confounders that could produce false positives.
        falsification_conditions: Conditions under which the hypothesis is rejected.
        required_evidence: What must be observed to confirm the hypothesis.
        created_at: Timestamp.
    """

    hypothesis_id: str
    experiment_id: str
    claim: str
    target_signal: str
    allowed_observables: list[str] = field(default_factory=list)
    expected_direction: str = "none"
    expected_effect: float = 0.0
    information_horizon: str = "t+1"
    confounders: list[str] = field(default_factory=list)
    falsification_conditions: list[str] = field(default_factory=list)
    required_evidence: list[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "hypothesis_id": self.hypothesis_id,
            "experiment_id": self.experiment_id,
            "claim": self.claim,
            "target_signal": self.target_signal,
            "allowed_observables": list(self.allowed_observables),
            "expected_direction": self.expected_direction,
            "expected_effect": self.expected_effect,
            "information_horizon": self.information_horizon,
            "confounders": list(self.confounders),
            "falsification_conditions": list(self.falsification_conditions),
            "required_evidence": list(self.required_evidence),
            "created_at": self.created_at,
        }

    def is_confirmed_by(self, observed_mechanism: str) -> bool:
        """Check whether an observed mechanism confirms the hypothesis.

        A hypothesis is confirmed ONLY if the observed mechanism matches
        the target signal. Profitability from a confounder does NOT confirm.

        Args:
            observed_mechanism: Description of what the agent actually found.

        Returns:
            True if the observed mechanism matches the target signal.
        """
        return observed_mechanism == self.target_signal

    def is_falsified_by(self, observed_mechanism: str) -> bool:
        """Check whether an observed mechanism falsifies the hypothesis.

        A hypothesis is falsified if the agent finds predictability from
        a confounder when the hypothesis claimed no predictability exists.

        Args:
            observed_mechanism: Description of what the agent actually found.

        Returns:
            True if the observed mechanism contradicts the hypothesis.
        """
        return observed_mechanism in self.confounders


# ---------------------------------------------------------------------------
# Factory functions for common hypothesis types
# ---------------------------------------------------------------------------


def create_null_hypothesis(
    experiment_id: str,
    hypothesis_id: str = "hypothesis-null",
) -> HypothesisArtifact:
    """Create a null hypothesis: no predictable pattern exists.

    This is the standard hypothesis for worlds with signal_strength=0.
    Any strategy that profits is either:
    1. Exploiting a confounder (e.g., autocorrelation)
    2. Manufacturing false discoveries through optimization pressure
    """
    return HypothesisArtifact(
        hypothesis_id=hypothesis_id,
        experiment_id=experiment_id,
        claim="No predictable pattern exists in returns",
        target_signal="none",
        allowed_observables=["close", "returns"],
        expected_direction="none",
        expected_effect=0.0,
        information_horizon="none",
        confounders=["autocorrelation", "momentum", "mean_reversion"],
        falsification_conditions=[
            "Agent finds Sharpe > 0.5 on research data",
            "Agent finds Sharpe > 0.0 on holdout data",
        ],
        required_evidence=[
            "Agent does not find statistically significant Sharpe",
            "Holdout performance consistent with random",
        ],
    )


def create_signal_hypothesis(
    experiment_id: str,
    signal_type: str,
    signal_strength: float,
    hypothesis_id: str = "hypothesis-signal",
) -> HypothesisArtifact:
    """Create a hypothesis that a specific signal exists.

    This is the standard hypothesis for worlds with signal_strength > 0.
    The agent must find the SPECIFIC signal, not just any predictability.
    """
    return HypothesisArtifact(
        hypothesis_id=hypothesis_id,
        experiment_id=experiment_id,
        claim=f"Returns are predictable from {signal_type} (strength={signal_strength})",
        target_signal=signal_type,
        allowed_observables=["close", "returns", "signal"],
        expected_direction="state_dependent",
        expected_effect=signal_strength * 0.5,
        information_horizon="t+1",
        confounders=["autocorrelation", "momentum"],
        falsification_conditions=[
            "Agent finds predictability but it comes from autocorrelation, not signal",
            "Agent's strategy does not correlate with the declared signal",
        ],
        required_evidence=[
            "Agent's strategy correlates with the declared signal",
            "Holdout performance is consistent with research performance",
            "Performance is not explained by autocorrelation alone",
        ],
    )
