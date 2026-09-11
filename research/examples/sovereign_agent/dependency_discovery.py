"""Dependency Discovery and Validation.

Mechanisms for discovering and validating dependencies.

Central distinctions:
    DEPENDENCY DISCOVERY ≠ DEPENDENCY VALIDATION ≠ DEPENDENCY GOVERNANCE ≠ DEPENDENCY AUTHORIZATION

Each mechanism has different epistemic status and authority.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from research.examples.sovereign_agent.dependency_status import (
    DependencyAttestation,
    DependencyDiscoveryMethod,
    DependencyEpistemicState,
    DependencyEpistemicStatus,
    DependencyScope,
    DependencyGraphEpistemicState,
    create_attestation,
)


class DiscoveryResult(str, Enum):
    """Result of a dependency discovery attempt."""
    DISCOVERED = "discovered"
    ALREADY_KNOWN = "already_known"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"
    FAILED = "failed"


class ValidationResult(str, Enum):
    """Result of dependency validation."""
    VALIDATED = "validated"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"


@dataclass(frozen=True)
class DiscoveryEvent:
    """An event where a dependency was discovered."""
    event_id: str
    timestamp: str
    dependency_id: str
    target_id: str
    method: DependencyDiscoveryMethod
    result: DiscoveryResult
    evidence: list[str] = field(default_factory=list)
    provenance: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class DependencyDiscoveryEngine:
    """Engine for discovering dependencies through various mechanisms."""

    def discover_from_static_analysis(
        self,
        source_code: str,
        target_id: str,
    ) -> DiscoveryEvent:
        """Discover dependencies through static analysis."""
        # Static analysis can identify references but not runtime necessity
        event = DiscoveryEvent(
            event_id=f"disc_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            dependency_id=f"dep_static_{uuid.uuid4().hex[:8]}",
            target_id=target_id,
            method=DependencyDiscoveryMethod.STATIC_ANALYSIS,
            result=DiscoveryResult.DISCOVERED,
            description=f"Static analysis found reference to {target_id}",
        )
        return event

    def discover_from_runtime_trace(
        self,
        trace: list[str],
        target_id: str,
    ) -> DiscoveryEvent:
        """Discover dependencies through runtime trace."""
        # Runtime traces show co-occurrence but not necessity
        target_found = any(target_id in t for t in trace)
        event = DiscoveryEvent(
            event_id=f"disc_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            dependency_id=f"dep_runtime_{uuid.uuid4().hex[:8]}",
            target_id=target_id,
            method=DependencyDiscoveryMethod.RUNTIME_TRACE,
            result=DiscoveryResult.DISCOVERED if target_found else DiscoveryResult.FAILED,
            evidence=trace,
            description=f"Runtime trace {'found' if target_found else 'did not find'} {target_id}",
        )
        return event

    def discover_from_controlled_intervention(
        self,
        target_id: str,
        intervention_result: bool,
    ) -> DiscoveryEvent:
        """Discover dependencies through controlled intervention."""
        # Controlled intervention can establish necessity
        event = DiscoveryEvent(
            event_id=f"disc_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            dependency_id=f"dep_intervention_{uuid.uuid4().hex[:8]}",
            target_id=target_id,
            method=DependencyDiscoveryMethod.CONTROLLED_INTERVENTION,
            result=DiscoveryResult.DISCOVERED if intervention_result else DiscoveryResult.REJECTED,
            description=f"Intervention on {target_id} {'confirmed' if intervention_result else 'rejected'} dependency",
        )
        return event

    def discover_from_counterfactual_test(
        self,
        target_id: str,
        counterfactual_result: bool,
    ) -> DiscoveryEvent:
        """Discover dependencies through counterfactual testing."""
        event = DiscoveryEvent(
            event_id=f"disc_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            dependency_id=f"dep_counterfactual_{uuid.uuid4().hex[:8]}",
            target_id=target_id,
            method=DependencyDiscoveryMethod.COUNTERFACTUAL_TEST,
            result=DiscoveryResult.DISCOVERED if counterfactual_result else DiscoveryResult.REJECTED,
            description=f"Counterfactual test on {target_id} {'confirmed' if counterfactual_result else 'rejected'} dependency",
        )
        return event

    def discover_from_model_hypothesis(
        self,
        target_id: str,
        hypothesis: str,
    ) -> DiscoveryEvent:
        """Discover dependencies from model hypothesis."""
        # Model hypotheses are NOT evidence
        event = DiscoveryEvent(
            event_id=f"disc_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            dependency_id=f"dep_hypothesis_{uuid.uuid4().hex[:8]}",
            target_id=target_id,
            method=DependencyDiscoveryMethod.MODEL_HYPOTHESIS,
            result=DiscoveryResult.INCONCLUSIVE,
            description=f"Model hypothesis about {target_id}: {hypothesis}",
        )
        return event

    def discover_from_documentation(
        self,
        target_id: str,
        doc_reference: str,
    ) -> DiscoveryEvent:
        """Discover dependencies from documentation."""
        # Documentation is NOT observed dependency
        event = DiscoveryEvent(
            event_id=f"disc_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            dependency_id=f"dep_doc_{uuid.uuid4().hex[:8]}",
            target_id=target_id,
            method=DependencyDiscoveryMethod.DOCUMENTATION,
            result=DiscoveryResult.INCONCLUSIVE,
            description=f"Documentation references {target_id}: {doc_reference}",
        )
        return event


@dataclass
class DependencyValidationEngine:
    """Engine for validating discovered dependencies."""

    def validate_dependency(
        self,
        dep_state: DependencyEpistemicState,
        validation_evidence: list[str],
        method: DependencyDiscoveryMethod,
    ) -> tuple[ValidationResult, DependencyAttestation]:
        """Validate a dependency using evidence."""
        # Different methods have different validation strength
        if method == DependencyDiscoveryMethod.CONTROLLED_INTERVENTION:
            # Controlled intervention provides strong validation
            attestation = create_attestation(
                attestor="validation_engine",
                method=method,
                status=DependencyEpistemicStatus.VALIDATED,
                confidence=0.9,
                evidence=validation_evidence,
            )
            return ValidationResult.VALIDATED, attestation

        if method == DependencyDiscoveryMethod.COUNTERFACTUAL_TEST:
            # Counterfactual testing provides strong validation
            attestation = create_attestation(
                attestor="validation_engine",
                method=method,
                status=DependencyEpistemicStatus.VALIDATED,
                confidence=0.85,
                evidence=validation_evidence,
            )
            return ValidationResult.VALIDATED, attestation

        if method == DependencyDiscoveryMethod.RUNTIME_TRACE:
            # Runtime traces only show co-occurrence, not necessity
            attestation = create_attestation(
                attestor="validation_engine",
                method=method,
                status=DependencyEpistemicStatus.OBSERVED,
                confidence=0.5,
                evidence=validation_evidence,
            )
            return ValidationResult.NEEDS_MORE_EVIDENCE, attestation

        if method == DependencyDiscoveryMethod.STATIC_ANALYSIS:
            # Static analysis shows reference, not runtime necessity
            attestation = create_attestation(
                attestor="validation_engine",
                method=method,
                status=DependencyEpistemicStatus.INFERRED,
                confidence=0.4,
                evidence=validation_evidence,
            )
            return ValidationResult.NEEDS_MORE_EVIDENCE, attestation

        if method == DependencyDiscoveryMethod.MODEL_HYPOTHESIS:
            # Model hypotheses are NOT evidence
            attestation = create_attestation(
                attestor="validation_engine",
                method=method,
                status=DependencyEpistemicStatus.HYPOTHESIZED,
                confidence=0.2,
                evidence=validation_evidence,
            )
            return ValidationResult.INCONCLUSIVE, attestation

        if method == DependencyDiscoveryMethod.DOCUMENTATION:
            # Documentation is NOT observed dependency
            attestation = create_attestation(
                attestor="validation_engine",
                method=method,
                status=DependencyEpistemicStatus.DECLARED,
                confidence=0.3,
                evidence=validation_evidence,
            )
            return ValidationResult.NEEDS_MORE_EVIDENCE, attestation

        # Default: needs more evidence
        attestation = create_attestation(
            attestor="validation_engine",
            method=method,
            status=DependencyEpistemicStatus.UNKNOWN,
            confidence=0.0,
            evidence=validation_evidence,
        )
        return ValidationResult.INCONCLUSIVE, attestation

    def reject_dependency(
        self,
        dep_state: DependencyEpistemicState,
        rejection_evidence: list[str],
        reason: str,
    ) -> DependencyAttestation:
        """Reject a dependency."""
        attestation = create_attestation(
            attestor="validation_engine",
            method=DependencyDiscoveryMethod.CONTROLLED_INTERVENTION,
            status=DependencyEpistemicStatus.REJECTED,
            confidence=0.9,
            evidence=rejection_evidence,
        )
        dep_state.add_attestation(attestation)
        dep_state.contradictions.extend(rejection_evidence)
        return attestation


def run_discovery_and_validation(
    target_id: str,
    method: DependencyDiscoveryMethod,
    evidence: list[str],
) -> tuple[DiscoveryEvent, ValidationResult, DependencyAttestation]:
    """Run discovery and validation for a target."""
    discovery_engine = DependencyDiscoveryEngine()
    validation_engine = DependencyValidationEngine()

    # Discover
    if method == DependencyDiscoveryMethod.STATIC_ANALYSIS:
        event = discovery_engine.discover_from_static_analysis("\n".join(evidence), target_id)
    elif method == DependencyDiscoveryMethod.RUNTIME_TRACE:
        event = discovery_engine.discover_from_runtime_trace(evidence, target_id)
    elif method == DependencyDiscoveryMethod.CONTROLLED_INTERVENTION:
        event = discovery_engine.discover_from_controlled_intervention(target_id, True)
    elif method == DependencyDiscoveryMethod.COUNTERFACTUAL_TEST:
        event = discovery_engine.discover_from_counterfactual_test(target_id, True)
    elif method == DependencyDiscoveryMethod.MODEL_HYPOTHESIS:
        event = discovery_engine.discover_from_model_hypothesis(target_id, "\n".join(evidence))
    elif method == DependencyDiscoveryMethod.DOCUMENTATION:
        event = discovery_engine.discover_from_documentation(target_id, "\n".join(evidence))
    else:
        event = DiscoveryEvent(
            event_id=f"disc_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            dependency_id=f"dep_{uuid.uuid4().hex[:8]}",
            target_id=target_id,
            method=method,
            result=DiscoveryResult.INCONCLUSIVE,
        )

    # Create dependency state
    dep_state = DependencyEpistemicState(
        dependency_id=event.dependency_id,
        target_id=target_id,
        current_status=DependencyEpistemicStatus.DECLARED,
        discovery_method=method,
    )

    # Validate
    val_result, attestation = validation_engine.validate_dependency(dep_state, evidence, method)
    dep_state.add_attestation(attestation)

    return event, val_result, attestation
