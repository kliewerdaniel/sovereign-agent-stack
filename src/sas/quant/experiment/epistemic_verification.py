"""Epistemic Verification — independent verification of epistemic states.

Implements the architectural boundary where the epistemic runtime itself
becomes independently verifiable.

The central research question:
    Can an epistemic state produced by one execution environment be
    independently verified from its immutable artifacts without trusting
    the process that originally produced the state?

Architecture:
    Evidence → Epistemic State Machine → Immutable State → Attestation
        → Independent Verification → Verified Epistemic State
        → Governance → Authorization → Execution

Invariants:
    A claim should not become authoritative because an agent says it is
    authoritative. It should become authoritative only through a derivation
    that an independent verifier can reconstruct from the underlying
    evidence, semantics, provenance, and authority rules.

    Integrity does not imply epistemic validity.
    Historical verification is distinct from current re-evaluation.
    Verification does not imply governance authorization.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import numpy as np

from sas.quant.experiment.typed_propositions import (
    EvidenceBundle,
    InterventionType,
    PropositionType,
    TypedProposition,
)
from sas.quant.experiment.evidence_structure import (
    EvidenceAccumulator,
    EvidenceDimension,
    EvidenceProfile,
    StructuredEvidenceBundle,
    evaluate_structured_proposition,
)
from sas.quant.experiment.epistemic_gaps import (
    EpistemicGap,
    GapType,
    GapResolvability,
    GapClosingPotential,
    EvidenceSufficiencyAssessment,
    analyze_evidence_gaps,
)
from sas.quant.experiment.epistemic_state import (
    EpistemicStatus,
    StateDimension,
    DimensionStatus,
    DimensionState,
    EpistemicState,
    TransitionType,
    EpistemicTransition,
    TransitionAuthorization,
    ReconciliationAssessment,
    EpistemicStateMachine,
    can_transition,
    reconcile_evidence_branches,
    create_initial_state,
    apply_evidence,
)


# ---------------------------------------------------------------------------
# Verification Result Types
# ---------------------------------------------------------------------------


class VerificationStatus(str, Enum):
    """Status of a verification attempt."""
    VALID = "valid"
    INVALID = "invalid"
    INCONCLUSIVE = "inconclusive"
    RECONSTRUCTABLE = "reconstructable"
    FORGED = "forged"
    PROVENANCE_MISMATCH = "provenance_mismatch"
    SEMANTICALLY_INVALID = "semantically_invalid"
    VERSION_MISMATCH = "version_mismatch"


class IntegrityCheck(str, Enum):
    """Types of integrity checks."""
    ARTIFACT_INTEGRITY = "artifact_integrity"
    PROVENANCE_VALID = "provenance_valid"
    TRANSITION_SEMANTICS = "transition_semantics"
    AUTHORITY_VALID = "authority_valid"
    STATE_RECONSTRUCTABLE = "state_reconstructable"
    LIFECYCLE_VALID = "lifecycle_valid"


# ---------------------------------------------------------------------------
# Epistemic Attestation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EpistemicAttestation:
    """Immutable attestation of an epistemic state.

    Contains the artifact references necessary for another verifier to
    reconstruct the basis of the status, WITHOUT trusting the original
    evaluator.

    Does NOT simply contain status = SUPPORTED. It contains the hashes
    needed to independently verify that status.
    """
    attestation_id: str

    # Hashes for integrity verification
    proposition_hash: str
    state_hash: str
    transition_hash: str

    # Artifact references
    evidence_hashes: list[str] = field(default_factory=list)
    experiment_hashes: list[str] = field(default_factory=list)
    intervention_hashes: list[str] = field(default_factory=list)

    # Versioning
    evaluator_version: str = "1.0.0"
    policy_version: str = "1.0.0"

    # Scope
    authority_scope: set[InterventionType] = field(default_factory=set)

    # Provenance
    provenance_root: str = ""

    # Verification requirements
    verification_requirements: list[str] = field(default_factory=list)

    # Self-hash
    attestation_hash: str = ""

    def compute_hash(self) -> str:
        """Compute the attestation hash from its contents."""
        content = json.dumps({
            "attestation_id": self.attestation_id,
            "proposition_hash": self.proposition_hash,
            "state_hash": self.state_hash,
            "transition_hash": self.transition_hash,
            "evidence_hashes": sorted(self.evidence_hashes),
            "experiment_hashes": sorted(self.experiment_hashes),
            "intervention_hashes": sorted(self.intervention_hashes),
            "evaluator_version": self.evaluator_version,
            "policy_version": self.policy_version,
            "authority_scope": sorted([v.value for v in self.authority_scope]),
            "provenance_root": self.provenance_root,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Verification Trace
# ---------------------------------------------------------------------------


@dataclass
class VerificationTrace:
    """Structured trace of the verification process.

    Provides a step-by-step record of what was verified and how.
    This trace is itself an immutable artifact once finalized.
    """
    trace_id: str
    attestation_id: str

    # Verification steps
    steps: list[dict] = field(default_factory=list)

    # Results
    proposition_valid: bool = False
    evidence_valid: bool = False
    provenance_valid: bool = False
    transition_valid: bool = False
    authority_valid: bool = False
    lifecycle_valid: bool = False
    state_reconstructable: bool = False

    # Discrepancies
    discrepancies: list[str] = field(default_factory=list)

    # Final result
    final_status: VerificationStatus = VerificationStatus.INCONCLUSIVE

    def add_step(self, check: str, passed: bool, detail: str = "") -> None:
        """Add a verification step."""
        self.steps.append({
            "check": check,
            "passed": passed,
            "detail": detail,
        })

    def explain(self) -> str:
        """Generate human-readable trace."""
        lines = [f"Verification Trace: {self.trace_id}"]
        lines.append(f"Attestation: {self.attestation_id}")
        lines.append("")
        for step in self.steps:
            status = "✓" if step["passed"] else "✗"
            lines.append(f"  {status} {step['check']}: {step['detail']}")
        lines.append("")
        if self.discrepancies:
            lines.append("Discrepancies:")
            for d in self.discrepancies:
                lines.append(f"  ✗ {d}")
            lines.append("")
        lines.append(f"Final Status: {self.final_status.value}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Verification Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VerificationResult:
    """Result of independent verification."""
    valid: bool
    status: VerificationStatus = VerificationStatus.INCONCLUSIVE

    # Detailed results
    proposition_valid: bool = False
    evidence_valid: bool = False
    provenance_valid: bool = False
    transition_valid: bool = False
    authority_valid: bool = False
    lifecycle_valid: bool = False
    state_reconstructable: bool = False

    # Discrepancies
    discrepancies: list[str] = field(default_factory=list)

    # Trace
    trace: Optional[VerificationTrace] = None

    # Verification metadata
    verifier_version: str = "1.0.0"
    verification_policy_version: str = "1.0.0"

    def explain(self) -> str:
        """Generate human-readable result."""
        lines = ["Verification Result"]
        lines.append(f"Valid: {self.valid}")
        lines.append(f"Status: {self.status.value}")
        lines.append("")
        lines.append(f"Proposition Valid: {self.proposition_valid}")
        lines.append(f"Evidence Valid: {self.evidence_valid}")
        lines.append(f"Provenance Valid: {self.provenance_valid}")
        lines.append(f"Transition Valid: {self.transition_valid}")
        lines.append(f"Authority Valid: {self.authority_valid}")
        lines.append(f"Lifecycle Valid: {self.lifecycle_valid}")
        lines.append(f"State Reconstructable: {self.state_reconstructable}")
        if self.discrepancies:
            lines.append("")
            lines.append("Discrepancies:")
            for d in self.discrepancies:
                lines.append(f"  ✗ {d}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Epistemic Verifier
# ---------------------------------------------------------------------------


class EpistemicVerifier:
    """Independent verifier of epistemic states.

    The verifier does NOT trust:
    - agent self-report
    - model output
    - evaluator claims
    - state labels
    - confidence values
    - execution environment claims

    It trusts only artifacts whose integrity and semantics it can
    independently validate.
    """

    def __init__(self, verifier_version: str = "1.0.0"):
        self.verifier_version = verifier_version
        self.policy_version = "1.0.0"

    def verify_attestation(
        self,
        attestation: EpistemicAttestation,
        artifacts: dict,
    ) -> VerificationResult:
        """Verify an attestation against its artifacts.

        This is the main entry point. It verifies:
        1. Proposition integrity
        2. Evidence integrity
        3. Provenance validity
        4. Transition semantics
        5. Authority validity
        6. State reconstructability
        """
        trace = VerificationTrace(
            trace_id=f"trace_{attestation.attestation_id}",
            attestation_id=attestation.attestation_id,
        )

        discrepancies = []

        # Step 1: Verify proposition integrity
        prop_valid = self._verify_proposition(attestation, artifacts, trace, discrepancies)

        # Step 2: Verify evidence integrity
        evidence_valid = self._verify_evidence(attestation, artifacts, trace, discrepancies)

        # Step 3: Verify provenance
        provenance_valid = self._verify_provenance(attestation, artifacts, trace, discrepancies)

        # Step 4: Verify transition semantics
        transition_valid = self._verify_transition_semantics(attestation, artifacts, trace, discrepancies)

        # Step 5: Verify authority
        authority_valid = self._verify_authority(attestation, artifacts, trace, discrepancies)

        # Step 6: Verify lifecycle
        lifecycle_valid = self._verify_lifecycle(attestation, artifacts, trace, discrepancies)

        # Step 7: Verify state reconstructability
        reconstructable = self._verify_state_reconstructable(attestation, artifacts, trace, discrepancies)

        # Determine final status
        all_valid = all([
            prop_valid,
            evidence_valid,
            provenance_valid,
            transition_valid,
            authority_valid,
            lifecycle_valid,
            reconstructable,
        ])

        if all_valid:
            final_status = VerificationStatus.VALID
        elif not prop_valid:
            final_status = VerificationStatus.FORGED
        elif not evidence_valid:
            final_status = VerificationStatus.PROVENANCE_MISMATCH
        elif not transition_valid:
            final_status = VerificationStatus.SEMANTICALLY_INVALID
        else:
            final_status = VerificationStatus.INVALID

        trace.proposition_valid = prop_valid
        trace.evidence_valid = evidence_valid
        trace.provenance_valid = provenance_valid
        trace.transition_valid = transition_valid
        trace.authority_valid = authority_valid
        trace.lifecycle_valid = lifecycle_valid
        trace.state_reconstructable = reconstructable
        trace.discrepancies = discrepancies
        trace.final_status = final_status

        return VerificationResult(
            valid=all_valid,
            status=final_status,
            proposition_valid=prop_valid,
            evidence_valid=evidence_valid,
            provenance_valid=provenance_valid,
            transition_valid=transition_valid,
            authority_valid=authority_valid,
            lifecycle_valid=lifecycle_valid,
            state_reconstructable=reconstructable,
            discrepancies=discrepancies,
            trace=trace,
            verifier_version=self.verifier_version,
        )

    def _verify_proposition(
        self,
        attestation: EpistemicAttestation,
        artifacts: dict,
        trace: VerificationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify proposition integrity."""
        proposition = artifacts.get("proposition")
        if proposition is None:
            trace.add_step("proposition", False, "Proposition artifact missing")
            discrepancies.append("Proposition artifact missing")
            return False

        # Verify proposition hash using same function as attestation builder
        prop_hash = _hash_proposition(proposition)
        if prop_hash != attestation.proposition_hash:
            trace.add_step("proposition", False, "Proposition hash mismatch")
            discrepancies.append(f"Proposition hash mismatch: expected {attestation.proposition_hash}, got {prop_hash}")
            return False

        trace.add_step("proposition", True, "Proposition hash verified")
        return True

    def _verify_evidence(
        self,
        attestation: EpistemicAttestation,
        artifacts: dict,
        trace: VerificationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify evidence integrity."""
        evidence_list = artifacts.get("evidence", [])
        if not evidence_list:
            trace.add_step("evidence", False, "No evidence artifacts provided")
            discrepancies.append("No evidence artifacts provided")
            return False

        # Verify each evidence hash using same function as attestation builder
        computed_hashes = []
        for bundle in evidence_list:
            bundle_hash = _hash_structured_evidence(bundle)
            computed_hashes.append(bundle_hash)

        # Check that all referenced evidence hashes are present
        attestation_hashes = set(attestation.evidence_hashes)
        computed_hashes_set = set(computed_hashes)

        missing = attestation_hashes - computed_hashes_set
        extra = computed_hashes_set - attestation_hashes

        if missing:
            trace.add_step("evidence", False, f"Missing evidence hashes: {missing}")
            discrepancies.append(f"Missing evidence: {missing}")
            return False

        if extra:
            trace.add_step("evidence", False, f"Extra evidence hashes: {extra}")
            discrepancies.append(f"Extra evidence: {extra}")
            return False

        trace.add_step("evidence", True, f"All {len(computed_hashes)} evidence hashes verified")
        return True

    def _verify_provenance(
        self,
        attestation: EpistemicAttestation,
        artifacts: dict,
        trace: VerificationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify provenance validity."""
        # Verify that the provenance root matches the evidence chain
        evidence_list = artifacts.get("evidence", [])
        if not evidence_list:
            trace.add_step("provenance", False, "No evidence for provenance verification")
            return False

        # Compute provenance root from evidence using same function as attestation builder
        evidence_hashes = [_hash_structured_evidence(b) for b in evidence_list]
        computed_root = _compute_provenance_root(evidence_hashes)

        if computed_root != attestation.provenance_root:
            trace.add_step("provenance", False, "Provenance root mismatch")
            discrepancies.append(f"Provenance root mismatch: expected {attestation.provenance_root}, got {computed_root}")
            return False

        trace.add_step("provenance", True, "Provenance root verified")
        return True

    def _verify_transition_semantics(
        self,
        attestation: EpistemicAttestation,
        artifacts: dict,
        trace: VerificationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify that transition semantics are valid.

        This checks that the transition actually follows from the evidence,
        not just that the hashes match.
        """
        transition = artifacts.get("transition")
        previous_state = artifacts.get("previous_state")
        evidence_list = artifacts.get("evidence", [])
        proposition = artifacts.get("proposition")

        if not all([transition, previous_state, evidence_list, proposition]):
            trace.add_step("transition", False, "Missing artifacts for transition verification")
            discrepancies.append("Missing artifacts for transition verification")
            return False

        # Re-run transition authorization
        auth = can_transition(previous_state, evidence_list, proposition)

        if not auth.allowed:
            trace.add_step("transition", False, "Transition not authorized")
            discrepancies.append(f"Transition not authorized: {auth.reasons}")
            return False

        # Verify that the transition's authority changes are justified
        # by the evidence's intervention types
        if transition and hasattr(transition, 'authority_added'):
            for authority_type, reason in transition.authority_added.items():
                # Check that at least one piece of evidence has authority
                has_authority = any(
                    proposition.accepts_evidence_from(b.intervention_type)
                    for b in evidence_list
                )
                if not has_authority:
                    trace.add_step("transition", False, f"Authority claimed without authorized evidence: {authority_type}")
                    discrepancies.append(f"Authority claimed without authorized evidence: {authority_type}")
                    return False

        trace.add_step("transition", True, "Transition semantics verified")
        return True

    def _verify_authority(
        self,
        attestation: EpistemicAttestation,
        artifacts: dict,
        trace: VerificationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify authority validity."""
        state = artifacts.get("state")
        proposition = artifacts.get("proposition")

        if not state or not proposition:
            trace.add_step("authority", False, "Missing state or proposition")
            discrepancies.append("Missing state or proposition for authority verification")
            return False

        # Verify that authority scope matches intervention types
        expected_scope = set()
        evidence_list = artifacts.get("evidence", [])
        for bundle in evidence_list:
            expected_scope.add(bundle.intervention_type)

        if state.authority_scope != expected_scope:
            trace.add_step("authority", False, "Authority scope mismatch")
            discrepancies.append(
                f"Authority scope mismatch: expected {expected_scope}, got {state.authority_scope}"
            )
            return False

        trace.add_step("authority", True, "Authority scope verified")
        return True

    def _verify_lifecycle(
        self,
        attestation: EpistemicAttestation,
        artifacts: dict,
        trace: VerificationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify lifecycle validity."""
        state = artifacts.get("state")
        if state is None:
            trace.add_step("lifecycle", False, "Missing state")
            return False

        # Verify parent state chain
        if state.parent_state_id is not None:
            parent = artifacts.get("previous_state")
            if parent is None:
                trace.add_step("lifecycle", False, "Parent state referenced but not provided")
                discrepancies.append("Parent state referenced but not provided")
                return False

            if parent.state_id != state.parent_state_id:
                trace.add_step("lifecycle", False, "Parent state ID mismatch")
                discrepancies.append(f"Parent state ID mismatch: expected {state.parent_state_id}, got {parent.state_id}")
                return False

        trace.add_step("lifecycle", True, "Lifecycle chain verified")
        return True

    def _verify_state_reconstructable(
        self,
        attestation: EpistemicAttestation,
        artifacts: dict,
        trace: VerificationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify that the state can be reconstructed from artifacts.

        The verifier independently reconstructs what the state SHOULD be
        given the evidence, then compares to the claimed state.
        """
        previous_state = artifacts.get("previous_state")
        evidence_list = artifacts.get("evidence", [])
        proposition = artifacts.get("proposition")
        claimed_state = artifacts.get("state")

        if not all([previous_state, evidence_list, proposition, claimed_state]):
            trace.add_step("reconstruct", False, "Missing artifacts for reconstruction")
            discrepancies.append("Missing artifacts for state reconstruction")
            return False

        # Independently reconstruct the state
        # Create a fresh state machine and apply evidence
        fresh_machine = EpistemicStateMachine(proposition)
        fresh_machine.states[previous_state.state_id] = previous_state
        fresh_machine.current_state_id = previous_state.state_id

        # Apply evidence through the fresh machine
        try:
            _, reconstructed_state = fresh_machine.apply_evidence(evidence_list)
        except Exception as e:
            trace.add_step("reconstruct", False, f"Reconstruction failed: {e}")
            discrepancies.append(f"State reconstruction failed: {e}")
            return False

        # Compare reconstructed state to claimed state
        # We compare key fields, not the full object (since IDs may differ)
        if reconstructed_state.status != claimed_state.status:
            trace.add_step("reconstruct", False, "Reconstructed status mismatch")
            discrepancies.append(
                f"Status mismatch: reconstructed {reconstructed_state.status.value}, "
                f"claimed {claimed_state.status.value}"
            )
            return False

        if set(reconstructed_state.evidence_refs) != set(claimed_state.evidence_refs):
            trace.add_step("reconstruct", False, "Reconstructed evidence refs mismatch")
            discrepancies.append("Evidence refs mismatch between reconstructed and claimed state")
            return False

        trace.add_step("reconstruct", True, "State independently reconstructed and verified")
        return True

    def _hash_artifact(self, artifact) -> str:
        """Compute hash of an artifact."""
        if hasattr(artifact, "provenance_hash"):
            return artifact.provenance_hash
        content = json.dumps(str(artifact), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _compute_merkle_root(self, hashes: list[str]) -> str:
        """Compute a simple Merkle root from hashes."""
        if not hashes:
            return ""
        current_level = sorted(hashes)
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = current_level[i] + current_level[i + 1]
                else:
                    combined = current_level[i] + current_level[i]
                next_level.append(hashlib.sha256(combined.encode()).hexdigest()[:16])
            current_level = next_level
        return current_level[0]


# ---------------------------------------------------------------------------
# Attestation Builder
# ---------------------------------------------------------------------------


def build_attestation(
    proposition: TypedProposition,
    state: EpistemicState,
    transition: EpistemicTransition,
    evidence: list[StructuredEvidenceBundle],
) -> EpistemicAttestation:
    """Build an attestation from artifacts."""
    evidence_hashes = [_hash_structured_evidence(e) for e in evidence]
    provenance_root = _compute_provenance_root(evidence_hashes)

    attestation = EpistemicAttestation(
        attestation_id=f"attestation_{state.state_id}",
        proposition_hash=_hash_proposition(proposition),
        state_hash=state.provenance_hash,
        transition_hash=transition.provenance_hash,
        evidence_hashes=evidence_hashes,
        experiment_hashes=[],  # Would be populated in full implementation
        intervention_hashes=[e.intervention_type.value for e in evidence],
        evaluator_version="1.0.0",
        policy_version="1.0.0",
        authority_scope=state.authority_scope,
        provenance_root=provenance_root,
        verification_requirements=[
            "proposition integrity",
            "evidence integrity",
            "provenance validity",
            "transition semantics",
            "authority validity",
            "lifecycle validity",
            "state reconstructability",
        ],
    )

    # Set attestation hash
    attestation = EpistemicAttestation(
        **{**dataclasses.asdict(attestation), "attestation_hash": attestation.compute_hash()}
    )

    return attestation


def _hash_proposition(prop: TypedProposition) -> str:
    """Hash a proposition."""
    content = json.dumps({
        "proposition_id": prop.proposition_id,
        "proposition_type": prop.proposition_type.value,
        "target": prop.target,
        "description": prop.description,
    }, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _hash_structured_evidence(bundle: StructuredEvidenceBundle) -> str:
    """Hash a structured evidence bundle."""
    content = json.dumps({
        "evidence_id": bundle.evidence_id,
        "intervention_type": bundle.intervention_type.value,
        "target": bundle.target,
        "effect_size": bundle.effect_size,
        "seed": bundle.seed,
        "time_period": bundle.time_period,
        "realization_id": bundle.realization_id,
    }, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _compute_provenance_root(evidence_hashes: list[str]) -> str:
    """Compute provenance root from evidence hashes."""
    if not evidence_hashes:
        return ""
    current_level = sorted(evidence_hashes)
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            if i + 1 < len(current_level):
                combined = current_level[i] + current_level[i + 1]
            else:
                combined = current_level[i] + current_level[i]
            next_level.append(hashlib.sha256(combined.encode()).hexdigest()[:16])
        current_level = next_level
    return current_level[0]


# ---------------------------------------------------------------------------
# Verification Entry Point
# ---------------------------------------------------------------------------


def verify_epistemic_state(
    attestation: EpistemicAttestation,
    proposition: TypedProposition,
    state: EpistemicState,
    transition: EpistemicTransition,
    previous_state: EpistemicState,
    evidence: list[StructuredEvidenceBundle],
) -> VerificationResult:
    """Convenience function to verify an epistemic state."""
    artifacts = {
        "proposition": proposition,
        "state": state,
        "transition": transition,
        "previous_state": previous_state,
        "evidence": evidence,
    }

    verifier = EpistemicVerifier()
    return verifier.verify_attestation(attestation, artifacts)
