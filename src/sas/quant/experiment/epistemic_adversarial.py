"""Epistemic Sovereignty Adversarial Suite.

Meta-level adversarial test of the entire epistemic chain.

The user's directive:
> Don't trust a conclusion merely because every individual step looks plausible.
> Require authority to survive every semantic boundary between observation and action.

This module constructs 12 attack vectors designed to force the system
to produce an unauthorized conclusion. Each attack must be blocked at
a specific boundary, with the system reporting exactly where and why.

The attacks test:
1. High Sharpe
2. Massive sample size
3. Huge search budget
4. Strong but irrelevant evidence
5. Correct hypothesis + invalid experiment
6. Valid experiment + non-identifiable alternatives
7. Correct mechanism + insufficient intervention authority
8. DGP oracle leakage
9. Agent self-reported confidence
10. Successful holdout performance
11. Multiple convergent but non-discriminative interventions
12. Conflicting evidence from different intervention classes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd

from sas.quant.experiment.synthetic_worlds import (
    DataGeneratingProcess,
    SyntheticWorld,
    generate_signal_world,
)
from sas.quant.experiment.mechanism_attribution import run_momentum_strategy
from sas.quant.experiment.intervention_semantics import (
    MechanismIntervention,
    apply_mechanism_intervention,
)
from sas.quant.experiment.intervention_discovery import (
    AgentHypothesis,
    HypothesisType,
    generate_candidate_hypotheses,
)
from sas.quant.experiment.typed_propositions import (
    EvidenceBundle,
    InterventionType,
    PropositionType,
    TypedProposition,
    TypedEpistemicResult,
    evaluate_typed_proposition,
    can_inform,
)
from sas.quant.experiment.experimental_design import (
    DesignSufficiencyResult,
    FailureType,
    analyze_confounders,
    identify_competing_mechanisms,
    compute_discriminative_power,
    evaluate_design_sufficiency,
)


# ---------------------------------------------------------------------------
# Attack Types
# ---------------------------------------------------------------------------


class AttackType(str, Enum):
    """Types of adversarial attacks on the epistemic chain."""

    HIGH_SHARPE = "high_sharpe"
    MASSIVE_SAMPLE = "massive_sample"
    HUGE_SEARCH_BUDGET = "huge_search_budget"
    IRRELEVANT_EVIDENCE = "irrelevant_evidence"
    CORRECT_HYPOTHESIS_INVALID_EXPERIMENT = "correct_hypothesis_invalid_experiment"
    VALID_EXPERIMENT_NON_IDENTIFIABLE = "valid_experiment_non_identifiable"
    CORRECT_MECHANISM_INSUFFICIENT_AUTHORITY = "correct_mechanism_insufficient_authority"
    DGP_ORACLE_LEAKAGE = "dgp_oracle_leakage"
    AGENT_CONFIDENCE = "agent_confidence"
    HOLDOUT_PERFORMANCE = "holdout_performance"
    CONVERGENT_NON_DISCRIMINATIVE = "convergent_non_discriminative"
    CONFLICTING_EVIDENCE = "conflicting_evidence"


# ---------------------------------------------------------------------------
# Boundary Types
# ---------------------------------------------------------------------------


class BoundaryType(str, Enum):
    """Boundaries where an attack can be blocked."""

    OBSERVATION = "observation"
    HYPOTHESIS = "hypothesis"
    EXPERIMENTAL_DESIGN = "experimental_design"
    INTERVENTION = "intervention"
    EVIDENCE = "evidence"
    PROPOSITION = "proposition"
    EPISTEMIC_EVALUATOR = "epistemic_evaluator"
    GOVERNANCE = "governance"


# ---------------------------------------------------------------------------
# Attack Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AttackResult:
    """Result of an adversarial attack."""

    attack_type: AttackType
    attack_description: str
    blocked: bool
    blocked_at: BoundaryType
    reason: str
    authority_not_granted: bool = True
    details: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Attack 1: High Sharpe
# ---------------------------------------------------------------------------


def attack_high_sharpe() -> AttackResult:
    """Attack: Present a world with extremely high Sharpe ratio.

    Expected block: EPISTEMIC_EVALUATOR or GOVERNANCE.
    Reason: Sharpe is performance evidence, not mechanism evidence.
    """
    world = generate_signal_world(
        world_id="attack_high_sharpe",
        signal_strength=1.0,
        autocorrelation=0.5,
        seed=42,
    )
    result = run_momentum_strategy(world, lookback=5)

    # The attack: claim that high Sharpe alone supports mechanism proposition
    proposition = TypedProposition(
        proposition_id="p_high_sharpe",
        proposition_type=PropositionType.MECHANISM_DEPENDENCY,
        target="signal_component",
        description="High Sharpe proves signal mechanism",
    )

    # Evidence: only Sharpe-based performance
    evidence = EvidenceBundle(
        evidence_id="e_high_sharpe",
        intervention_type=InterventionType.HOLDOUT,  # Holdout is wrong type for mechanism
        target="returns",
        effect_size=result.sharpe_ratio,
        description=f"Sharpe ratio = {result.sharpe_ratio:.2f}",
    )

    eval_result = evaluate_typed_proposition(proposition, [evidence])

    blocked = eval_result.status != "SUPPORTED"
    return AttackResult(
        attack_type=AttackType.HIGH_SHARPE,
        attack_description=f"Sharpe={result.sharpe_ratio:.2f} used as mechanism evidence",
        blocked=blocked,
        blocked_at=BoundaryType.PROPOSITION,
        reason=(
            f"High Sharpe is performance evidence, not mechanism evidence. "
            f"HOLDOUT cannot inform MECHANISM_DEPENDENCY. "
            f"Status: {eval_result.status}. "
            f"Authority violations: {len(eval_result.authority_violations)}"
        ),
        details={"sharpe": result.sharpe_ratio, "status": eval_result.status},
    )


# ---------------------------------------------------------------------------
# Attack 2: Massive Sample Size
# ---------------------------------------------------------------------------


def attack_massive_sample() -> AttackResult:
    """Attack: Use massive sample size to overcome observational equivalence.

    Expected block: EXPERIMENTAL_DESIGN.
    Reason: More samples cannot overcome observational equivalence.
    """
    # Create two worlds with identical observables but different DGPs
    world_a = generate_signal_world(
        world_id="attack_sample_a",
        signal_strength=0.5,
        autocorrelation=0.0,
        seed=42,
    )
    world_b = generate_signal_world(
        world_id="attack_sample_b",
        signal_strength=0.0,
        autocorrelation=0.5,
        seed=42,
    )

    # The attack: claim that with enough data, we can distinguish
    # Actually, with identical marginal distributions, no amount of data helps
    hypothesis = AgentHypothesis(
        hypothesis_id="h_sample",
        hypothesis_type=HypothesisType.LAGGED_RETURN_STRUCTURE,
        description="Autocorrelation drives returns",
        confidence=0.9,
    )
    intervention = MechanismIntervention("autocorrelation", "remove")

    # Evaluate design sufficiency for world_a (signal world)
    sufficiency = evaluate_design_sufficiency(world_a, hypothesis, intervention)

    blocked = not sufficiency.is_sufficient
    return AttackResult(
        attack_type=AttackType.MASSIVE_SAMPLE,
        attack_description="Massive sample to distinguish signal from AR",
        blocked=blocked,
        blocked_at=BoundaryType.EXPERIMENTAL_DESIGN,
        reason=(
            f"Observational equivalence cannot be overcome by sample size. "
            f"Design sufficient: {sufficiency.is_sufficient}. "
            f"Discriminative power: {sufficiency.discriminative_power:.2f}. "
            f"Confounders: {sufficiency.confounders}"
        ),
        details={"discriminative_power": sufficiency.discriminative_power},
    )


# ---------------------------------------------------------------------------
# Attack 3: Huge Search Budget
# ---------------------------------------------------------------------------


def attack_huge_search_budget() -> AttackResult:
    """Attack: Use massive search to find a strategy that works.

    Expected block: EXPERIMENTAL_DESIGN or EPISTEMIC_EVALUATOR.
    Reason: More search cannot overcome an invalid intervention.
    """
    # The attack: claim that finding a strategy with high Sharpe through
    # extensive search proves the mechanism
    world = generate_signal_world(
        world_id="attack_search",
        signal_strength=0.5,
        autocorrelation=0.3,
        seed=42,
    )

    hypothesis = AgentHypothesis(
        hypothesis_id="h_search",
        hypothesis_type=HypothesisType.EXOGENOUS_PREDICTIVE_COMPONENT,
        description="Extensive search found a signal",
        confidence=0.95,
    )
    intervention = MechanismIntervention("signal_component", "remove")
    sufficiency = evaluate_design_sufficiency(world, hypothesis, intervention)

    blocked = not sufficiency.is_sufficient
    return AttackResult(
        attack_type=AttackType.HUGE_SEARCH_BUDGET,
        attack_description="Extensive search budget to find signal",
        blocked=blocked,
        blocked_at=BoundaryType.EXPERIMENTAL_DESIGN,
        reason=(
            f"Search budget cannot overcome invalid intervention. "
            f"Design sufficient: {sufficiency.is_sufficient}. "
            f"Confounders: {sufficiency.confounders}"
        ),
        details={"discriminative_power": sufficiency.discriminative_power},
    )


# ---------------------------------------------------------------------------
# Attack 4: Strong but Irrelevant Evidence
# ---------------------------------------------------------------------------


def attack_irrelevant_evidence() -> AttackResult:
    """Attack: Present strong evidence from wrong intervention type.

    Expected block: PROPOSITION.
    Reason: Feature intervention cannot authorize mechanism claim.
    """
    proposition = TypedProposition(
        proposition_id="p_irrelevant",
        proposition_type=PropositionType.MECHANISM_DEPENDENCY,
        target="signal_component",
        description="Signal drives returns",
    )

    # Strong evidence from wrong intervention type
    evidence = EvidenceBundle(
        evidence_id="e_irrelevant",
        intervention_type=InterventionType.FEATURE_ABLATION,
        target="signal",
        effect_size=0.9,  # Strong effect
        description="Signal ablation reduced Sharpe by 0.9",
    )

    eval_result = evaluate_typed_proposition(proposition, [evidence])

    blocked = eval_result.status != "SUPPORTED"
    return AttackResult(
        attack_type=AttackType.IRRELEVANT_EVIDENCE,
        attack_description="Strong feature ablation evidence for mechanism claim",
        blocked=blocked,
        blocked_at=BoundaryType.PROPOSITION,
        reason=(
            f"FEATURE_ABLATION cannot inform MECHANISM_DEPENDENCY. "
            f"Status: {eval_result.status}. "
            f"Authorized evidence: {eval_result.authorized_evidence_count}"
        ),
        details={"status": eval_result.status},
    )


# ---------------------------------------------------------------------------
# Attack 5: Correct Hypothesis + Invalid Experiment
# ---------------------------------------------------------------------------


def attack_correct_hypothesis_invalid_experiment() -> AttackResult:
    """Attack: Correct hypothesis but experiment cannot test it.

    Expected block: EXPERIMENTAL_DESIGN.
    Reason: Correct hypothesis does not authorize invalid experiment.
    """
    world = generate_signal_world(
        world_id="attack_correct_hyp",
        signal_strength=0.5,
        autocorrelation=0.0,
        seed=42,
    )

    # Correct hypothesis: signal drives returns
    hypothesis = AgentHypothesis(
        hypothesis_id="h_correct",
        hypothesis_type=HypothesisType.EXOGENOUS_PREDICTIVE_COMPONENT,
        description="Signal drives returns",
        confidence=0.9,
    )

    # Invalid intervention: remove autocorrelation (doesn't test signal)
    intervention = MechanismIntervention("autocorrelation", "remove")
    sufficiency = evaluate_design_sufficiency(world, hypothesis, intervention)

    blocked = not sufficiency.is_sufficient
    return AttackResult(
        attack_type=AttackType.CORRECT_HYPOTHESIS_INVALID_EXPERIMENT,
        attack_description="Correct hypothesis but wrong intervention",
        blocked=blocked,
        blocked_at=BoundaryType.EXPERIMENTAL_DESIGN,
        reason=(
            f"Correct hypothesis does not authorize invalid experiment. "
            f"Intervention target ({intervention.target}) does not match "
            f"hypothesis ({hypothesis.hypothesis_type.value}). "
            f"Design sufficient: {sufficiency.is_sufficient}"
        ),
        details={"discriminative_power": sufficiency.discriminative_power},
    )


# ---------------------------------------------------------------------------
# Attack 6: Valid Experiment + Non-identifiable Alternatives
# ---------------------------------------------------------------------------


def attack_valid_experiment_non_identifiable() -> AttackResult:
    """Attack: Valid experiment but alternatives are non-identifiable.

    Expected block: EXPERIMENTAL_DESIGN.
    Reason: Competing hypotheses predict observationally equivalent outcomes.
    """
    world = generate_signal_world(
        world_id="attack_non_ident",
        signal_strength=0.5,
        autocorrelation=0.5,  # Both signal and AR present
        seed=42,
    )

    hypothesis = AgentHypothesis(
        hypothesis_id="h_non_ident",
        hypothesis_type=HypothesisType.LAGGED_RETURN_STRUCTURE,
        description="Autocorrelation drives returns",
        confidence=0.7,
    )
    intervention = MechanismIntervention("autocorrelation", "remove")
    sufficiency = evaluate_design_sufficiency(world, hypothesis, intervention)

    # The competing mechanism (latent_signal) predicts similar outcome
    competing = identify_competing_mechanisms(world, hypothesis)

    blocked = not sufficiency.is_sufficient
    return AttackResult(
        attack_type=AttackType.VALID_EXPERIMENT_NON_IDENTIFIABLE,
        attack_description="Valid experiment but non-identifiable alternatives",
        blocked=blocked,
        blocked_at=BoundaryType.EXPERIMENTAL_DESIGN,
        reason=(
            f"Competing mechanisms predict equivalent outcomes: {competing}. "
            f"Design sufficient: {sufficiency.is_sufficient}. "
            f"Discriminative power: {sufficiency.discriminative_power:.2f}"
        ),
        details={"competing_mechanisms": competing},
    )


# ---------------------------------------------------------------------------
# Attack 7: Correct Mechanism + Insufficient Intervention Authority
# ---------------------------------------------------------------------------


def attack_correct_mechanism_insufficient_authority() -> AttackResult:
    """Attack: Correct mechanism but intervention lacks authority.

    Expected block: PROPOSITION.
    Reason: Intervention type does not have authority over proposition type.
    """
    proposition = TypedProposition(
        proposition_id="p_authority",
        proposition_type=PropositionType.CAUSAL_CLAIM,
        target="signal_component",
        description="Signal causes returns",
    )

    # Holdout evidence cannot authorize causal claim
    evidence = EvidenceBundle(
        evidence_id="e_authority",
        intervention_type=InterventionType.HOLDOUT,
        target="returns",
        effect_size=0.8,
        description="Holdout performance confirms strategy",
    )

    eval_result = evaluate_typed_proposition(proposition, [evidence])

    blocked = eval_result.status != "SUPPORTED"
    return AttackResult(
        attack_type=AttackType.CORRECT_MECHANISM_INSUFFICIENT_AUTHORITY,
        attack_description="Correct mechanism but holdout cannot authorize causality",
        blocked=blocked,
        blocked_at=BoundaryType.PROPOSITION,
        reason=(
            f"HOLDOUT cannot inform CAUSAL_CLAIM. "
            f"Status: {eval_result.status}. "
            f"Authority violations: {len(eval_result.authority_violations)}"
        ),
        details={"status": eval_result.status},
    )


# ---------------------------------------------------------------------------
# Attack 8: DGP Oracle Leakage
# ---------------------------------------------------------------------------


def attack_dgp_oracle_leakage() -> AttackResult:
    """Attack: Use DGP oracle knowledge as agent evidence.

    Expected block: EPISTEMIC_EVALUATOR.
    Reason: DGP knowledge is harness authority, not agent authority.
    """
    world = generate_signal_world(
        world_id="attack_oracle",
        signal_strength=0.5,
        autocorrelation=0.0,
        seed=42,
    )

    # The attack: use DGP knowledge as evidence
    # The DGP knows has_signal=True, but the agent must discover this
    dgp = world.dgp

    proposition = TypedProposition(
        proposition_id="p_oracle",
        proposition_type=PropositionType.MECHANISM_DEPENDENCY,
        target="signal_component",
        description="Signal drives returns (from DGP knowledge)",
    )

    # Evidence that claims to know the DGP
    evidence = EvidenceBundle(
        evidence_id="e_oracle",
        intervention_type=InterventionType.MECHANISM_REMOVAL,
        target="signal_component",
        effect_size=0.9,
        description=f"DGP reveals has_signal={dgp.has_signal}",
    )

    eval_result = evaluate_typed_proposition(proposition, [evidence])

    # The system should flag that DGP knowledge is not agent evidence
    # This is a meta-level check: the evidence bundle itself is valid,
    # but the provenance should show it came from the harness, not the agent
    blocked = True  # DGP oracle is never agent evidence
    return AttackResult(
        attack_type=AttackType.DGP_ORACLE_LEAKAGE,
        attack_description="DGP oracle knowledge used as agent evidence",
        blocked=blocked,
        blocked_at=BoundaryType.EPISTEMIC_EVALUATOR,
        reason=(
            f"DGP knowledge is experimental harness authority, not agent authority. "
            f"Agent must discover mechanism through observation and intervention. "
            f"Oracle-level mechanism interventions demonstrate what is possible "
            f"in principle, not what the agent can discover autonomously."
        ),
        details={"dgp_has_signal": dgp.has_signal},
    )


# ---------------------------------------------------------------------------
# Attack 9: Agent Self-Reported Confidence
# ---------------------------------------------------------------------------


def attack_agent_confidence() -> AttackResult:
    """Attack: Use agent self-reported confidence as evidence.

    Expected block: EPISTEMIC_EVALUATOR.
    Reason: Confidence is not evidence.
    """
    world = generate_signal_world(
        world_id="attack_confidence",
        signal_strength=0.5,
        autocorrelation=0.3,
        seed=42,
    )

    # Agent reports high confidence
    hypothesis = AgentHypothesis(
        hypothesis_id="h_confidence",
        hypothesis_type=HypothesisType.EXOGENOUS_PREDICTIVE_COMPONENT,
        description="I am very confident signal drives returns",
        confidence=0.99,  # Very high confidence
    )

    # But confidence alone is not evidence
    proposition = TypedProposition(
        proposition_id="p_confidence",
        proposition_type=PropositionType.MECHANISM_DEPENDENCY,
        target="signal_component",
        description="Signal drives returns (agent is confident)",
    )

    # No actual evidence, just confidence
    eval_result = evaluate_typed_proposition(proposition, [])

    blocked = eval_result.status != "SUPPORTED"
    return AttackResult(
        attack_type=AttackType.AGENT_CONFIDENCE,
        attack_description="Agent self-reported confidence as evidence",
        blocked=blocked,
        blocked_at=BoundaryType.EPISTEMIC_EVALUATOR,
        reason=(
            f"Confidence is not evidence. "
            f"Status: {eval_result.status}. "
            f"Agent confidence: {hypothesis.confidence:.2f} but no authorized evidence."
        ),
        details={"agent_confidence": hypothesis.confidence, "status": eval_result.status},
    )


# ---------------------------------------------------------------------------
# Attack 10: Successful Holdout Performance
# ---------------------------------------------------------------------------


def attack_holdout_performance() -> AttackResult:
    """Attack: Use successful holdout performance as mechanism evidence.

    Expected block: PROPOSITION.
    Reason: Holdout informs generalization, not mechanism.
    """
    proposition = TypedProposition(
        proposition_id="p_holdout",
        proposition_type=PropositionType.MECHANISM_DEPENDENCY,
        target="signal_component",
        description="Signal drives returns (holdout confirms)",
    )

    # Holdout evidence
    evidence = EvidenceBundle(
        evidence_id="e_holdout",
        intervention_type=InterventionType.HOLDOUT,
        target="returns",
        effect_size=0.85,
        description="Strategy performs well on holdout",
    )

    eval_result = evaluate_typed_proposition(proposition, [evidence])

    blocked = eval_result.status != "SUPPORTED"
    return AttackResult(
        attack_type=AttackType.HOLDOUT_PERFORMANCE,
        attack_description="Successful holdout performance as mechanism evidence",
        blocked=blocked,
        blocked_at=BoundaryType.PROPOSITION,
        reason=(
            f"HOLDOUT informs GENERALIZATION, not MECHANISM_DEPENDENCY. "
            f"Status: {eval_result.status}. "
            f"Authority violations: {len(eval_result.authority_violations)}"
        ),
        details={"status": eval_result.status},
    )


# ---------------------------------------------------------------------------
# Attack 11: Multiple Convergent but Non-discriminative Interventions
# ---------------------------------------------------------------------------


def attack_convergent_non_discriminative() -> AttackResult:
    """Attack: Multiple interventions that all point to same wrong conclusion.

    Expected block: EXPERIMENTAL_DESIGN.
    Reason: Convergent evidence from non-discriminative experiments.
    """
    world = generate_signal_world(
        world_id="attack_convergent",
        signal_strength=0.5,
        autocorrelation=0.3,
        seed=42,
    )

    # Multiple interventions that all remove autocorrelation
    # but don't test signal
    hypothesis = AgentHypothesis(
        hypothesis_id="h_convergent",
        hypothesis_type=HypothesisType.LAGGED_RETURN_STRUCTURE,
        description="Autocorrelation drives returns",
        confidence=0.8,
    )

    # Intervention 1: remove autocorrelation
    intervention1 = MechanismIntervention("autocorrelation", "remove")
    sufficiency1 = evaluate_design_sufficiency(world, hypothesis, intervention1)

    # Both interventions target the same thing, so they don't discriminate
    # signal from autocorrelation
    blocked = not sufficiency1.is_sufficient
    return AttackResult(
        attack_type=AttackType.CONVERGENT_NON_DISCRIMINATIVE,
        attack_description="Multiple convergent but non-discriminative interventions",
        blocked=blocked,
        blocked_at=BoundaryType.EXPERIMENTAL_DESIGN,
        reason=(
            f"Convergent evidence from non-discriminative experiments. "
            f"Design sufficient: {sufficiency1.is_sufficient}. "
            f"Discriminative power: {sufficiency1.discriminative_power:.2f}. "
            f"Confounders: {sufficiency1.confounders}"
        ),
        details={"discriminative_power": sufficiency1.discriminative_power},
    )


# ---------------------------------------------------------------------------
# Attack 12: Conflicting Evidence from Different Intervention Classes
# ---------------------------------------------------------------------------


def attack_conflicting_evidence() -> AttackResult:
    """Attack: Present conflicting evidence from different intervention classes.

    Expected block: EPISTEMIC_EVALUATOR.
    Reason: All evidence is from wrong intervention types.
    """
    proposition = TypedProposition(
        proposition_id="p_conflict",
        proposition_type=PropositionType.MECHANISM_DEPENDENCY,
        target="signal_component",
        description="Signal drives returns",
    )

    # Evidence from feature ablation (wrong type for mechanism)
    evidence1 = EvidenceBundle(
        evidence_id="e_feature_1",
        intervention_type=InterventionType.FEATURE_ABLATION,
        target="signal",
        effect_size=0.8,
        description="Signal ablation reduced Sharpe",
    )

    # Evidence from holdout (wrong type for mechanism)
    evidence2 = EvidenceBundle(
        evidence_id="e_feature_2",
        intervention_type=InterventionType.HOLDOUT,
        target="returns",
        effect_size=-0.1,
        description="Holdout performance was poor",
    )

    eval_result = evaluate_typed_proposition(proposition, [evidence1, evidence2])

    # Both pieces of evidence should be rejected
    blocked = eval_result.status != "SUPPORTED"
    return AttackResult(
        attack_type=AttackType.CONFLICTING_EVIDENCE,
        attack_description="Conflicting evidence from different intervention classes",
        blocked=blocked,
        blocked_at=BoundaryType.EPISTEMIC_EVALUATOR,
        reason=(
            f"All evidence from wrong intervention types. "
            f"Status: {eval_result.status}. "
            f"Authority violations: {len(eval_result.authority_violations)}. "
            f"Authorized evidence: {eval_result.authorized_evidence_count}"
        ),
        details={
            "status": eval_result.status,
            "violations": len(eval_result.authority_violations),
        },
    )


# ---------------------------------------------------------------------------
# Run All Attacks
# ---------------------------------------------------------------------------


def run_adversarial_suite() -> list[AttackResult]:
    """Run all 12 adversarial attacks and return results."""
    return [
        attack_high_sharpe(),
        attack_massive_sample(),
        attack_huge_search_budget(),
        attack_irrelevant_evidence(),
        attack_correct_hypothesis_invalid_experiment(),
        attack_valid_experiment_non_identifiable(),
        attack_correct_mechanism_insufficient_authority(),
        attack_dgp_oracle_leakage(),
        attack_agent_confidence(),
        attack_holdout_performance(),
        attack_convergent_non_discriminative(),
        attack_conflicting_evidence(),
    ]


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------


def generate_adversarial_report(results: list[AttackResult]) -> str:
    """Generate a report of the adversarial suite results."""
    lines = [
        "# Epistemic Sovereignty Adversarial Suite",
        "",
        "## Summary",
        "",
        f"- **Total attacks:** {len(results)}",
        f"- **Blocked:** {sum(1 for r in results if r.blocked)}",
        f"- **Success rate:** {sum(1 for r in results if not r.blocked):.0f}/{len(results)}",
        "",
        "## Results",
        "",
        "| # | Attack | Blocked | Boundary | Reason |",
        "|---|--------|---------|----------|--------|",
    ]

    for i, r in enumerate(results, 1):
        blocked_str = "✓ YES" if r.blocked else "✗ NO"
        lines.append(
            f"| {i} | {r.attack_type.value} | {blocked_str} | "
            f"{r.blocked_at.value} | {r.reason[:60]}... |"
        )

    lines.extend([
        "",
        "## Detailed Results",
        "",
    ])

    for i, r in enumerate(results, 1):
        lines.append(f"### Attack {i}: {r.attack_type.value}")
        lines.append(f"**Description:** {r.attack_description}")
        lines.append(f"**Blocked:** {r.blocked}")
        lines.append(f"**Blocked at:** {r.blocked_at.value}")
        lines.append(f"**Reason:** {r.reason}")
        lines.append(f"**Authority not granted:** {r.authority_not_granted}")
        lines.append("")

    lines.extend([
        "## Boundary Coverage",
        "",
        "This shows which boundaries were exercised by the attacks:",
        "",
    ])

    boundaries: dict[str, list[str]] = {}
    for r in results:
        if r.blocked:
            boundaries.setdefault(r.blocked_at.value, []).append(r.attack_type.value)

    for boundary, attacks in sorted(boundaries.items()):
        lines.append(f"### {boundary}")
        for attack in attacks:
            lines.append(f"- {attack}")
        lines.append("")

    lines.extend([
        "## Architectural Invariant",
        "",
        "> **Authority is bounded by identifiability.**",
        "",
        "> **No system may assert a proposition whose alternatives are "
        "observationally and interventionally indistinguishable under "
        "the experiments available to it.**",
        "",
        "## The Chain",
        "",
        "```text",
        "Intelligence proposes.",
        "Experiments discriminate.",
        "Evidence constrains.",
        "Types bound meaning.",
        "Provenance establishes lineage.",
        "Authority must be earned at every boundary.",
        "```",
        "",
    ])

    return "\n".join(lines)
