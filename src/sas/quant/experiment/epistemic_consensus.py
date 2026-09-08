"""Epistemic Consensus, Verifier Disagreement, and Authority Reconciliation.

Implements the architectural boundary where multiple independent verifiers
may disagree about epistemic states, and the system must determine what
it is actually entitled to conclude from that disagreement.

The central research question:
    What is the epistemic meaning of disagreement between independently
    valid verifiers?

Architecture:
    Evidence → Epistemic State Machine → Immutable State → Attestation
        → Multiple Independent Verifiers → Verification Assertions
        → Structured Comparison → Agreement / Divergence Classification
        → Epistemic Conflict or Consensus Artifact
        → Governance → Authorization → Execution

Invariants:
    Verifier agreement is not epistemic truth.
    Verifier disagreement is itself an epistemic artifact.
    Identity multiplicity does not imply epistemic independence.
    Consensus cannot be stronger than the independence of its constituent verifiers.
    Historical verification does not imply current semantic agreement.
    A valid minority disagreement must not be erased by majority consensus.
    An unresolved verifier disagreement is not equivalent to refutation.
    Evidence divergence is distinct from verification disagreement.
    Semantic divergence is distinct from implementation disagreement.
    Governance disagreement does not invalidate epistemic agreement.
    Consensus is a derived artifact, not an authority root.
    Epistemic independence must be established by provenance rather than asserted.
    A verifier cannot inherit authority merely by inheriting another's identity.
    No epistemic authority may increase solely because more identities repeat
    the same conclusion.
    Independent disagreement must preserve uncertainty rather than manufacture
    certainty.
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
from sas.quant.experiment.epistemic_verification import (
    VerificationStatus,
    IntegrityCheck,
    EpistemicAttestation,
    VerificationTrace,
    VerificationResult,
    EpistemicVerifier,
    build_attestation,
    verify_epistemic_state,
    _hash_proposition,
    _hash_structured_evidence,
    _compute_provenance_root,
)


# ---------------------------------------------------------------------------
# Verifier Identity
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VerifierIdentity:
    """Immutable identity of a verifier.

    Identifies which verifier and semantic regime produced a verification
    result. Does NOT itself establish epistemic authority.

    The identity only identifies:
    > Which verifier and semantic regime produced this verification result?

    It does NOT establish trust, authority, or correctness.
    """
    verifier_id: str
    implementation_id: str
    implementation_version: str = "1.0.0"
    epistemic_rule_version: str = "1.0.0"
    proposition_semantics_version: str = "1.0.0"
    intervention_semantics_version: str = "1.0.0"
    provenance_rules_version: str = "1.0.0"
    lifecycle_rules_version: str = "1.0.0"

    def compute_hash(self) -> str:
        """Compute hash of the identity."""
        content = json.dumps({
            "verifier_id": self.verifier_id,
            "implementation_id": self.implementation_id,
            "implementation_version": self.implementation_version,
            "epistemic_rule_version": self.epistemic_rule_version,
            "proposition_semantics_version": self.proposition_semantics_version,
            "intervention_semantics_version": self.intervention_semantics_version,
            "provenance_rules_version": self.provenance_rules_version,
            "lifecycle_rules_version": self.lifecycle_rules_version,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Verifier Independence Relationship
# ---------------------------------------------------------------------------


class IndependenceRelationship(str, Enum):
    """Relationship between two verifiers."""
    INDEPENDENT = "independent"
    DERIVED_FROM = "derived_from"
    WRAPS = "wraps"
    REUSES = "reuses"
    SHARES_IMPLEMENTATION = "shares_implementation"
    SHARES_RULE_ENGINE = "shares_rule_engine"
    SHARES_EVALUATOR = "shares_evaluator"
    SHARES_EVIDENCE = "shares_evidence"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Verification Assertion
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VerificationAssertion:
    """Immutable structure representing what a verifier actually established.

    Does NOT simply store status = SUPPORTED. It preserves the derivation
    basis so that another verifier can reconstruct what was established.

    A verifier should be able to say:
        mechanism = VERIFIED
        generalization = UNRESOLVED
        causal_authority = ABSENT

    rather than collapsing the entire epistemic state into one label.
    """
    assertion_id: str
    verifier_identity: VerifierIdentity
    attestation_hash: str

    # Dimension-specific results
    verified_dimensions: dict[StateDimension, DimensionStatus] = field(default_factory=dict)
    failed_dimensions: dict[StateDimension, str] = field(default_factory=dict)
    unresolved_dimensions: dict[StateDimension, str] = field(default_factory=dict)

    # Verification trace
    verification_trace_hash: str = ""

    # Semantic versions used
    semantic_rule_version: str = "1.0.0"

    # Artifact references
    evidence_refs: list[str] = field(default_factory=list)
    provenance_refs: list[str] = field(default_factory=list)

    # Result
    overall_status: VerificationStatus = VerificationStatus.INCONCLUSIVE

    # Self-hash
    result_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the assertion."""
        content = json.dumps({
            "assertion_id": self.assertion_id,
            "verifier_identity_hash": self.verifier_identity.compute_hash(),
            "attestation_hash": self.attestation_hash,
            "verified_dimensions": {k.value: v.value for k, v in self.verified_dimensions.items()},
            "failed_dimensions": {k.value: v for k, v in self.failed_dimensions.items()},
            "unresolved_dimensions": {k.value: v for k, v in self.unresolved_dimensions.items()},
            "verification_trace_hash": self.verification_trace_hash,
            "semantic_rule_version": self.semantic_rule_version,
            "evidence_refs": sorted(self.evidence_refs),
            "provenance_refs": sorted(self.provenance_refs),
            "overall_status": self.overall_status.value,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Disagreement Classes
# ---------------------------------------------------------------------------


class DisagreementClass(str, Enum):
    """Taxonomy of disagreement types between verifiers."""
    AGREEMENT = "agreement"
    EVIDENCE_DIVERGENCE = "evidence_divergence"
    PROVENANCE_DIVERGENCE = "provenance_divergence"
    SEMANTIC_DIVERGENCE = "semantic_divergence"
    RULE_VERSION_DIVERGENCE = "rule_version_divergence"
    AUTHORITY_POLICY_DIVERGENCE = "authority_policy_divergence"
    LIFECYCLE_DIVERGENCE = "lifecycle_divergence"
    RECONSTRUCTION_DIVERGENCE = "reconstruction_divergence"
    UNRESOLVED_VERIFICATION_CONFLICT = "unresolved_verification_conflict"


# ---------------------------------------------------------------------------
# Verifier Comparison
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VerifierComparison:
    """Deterministic comparison of two verification assertions.

    Operates structurally, not just on final status labels.
    """
    comparison_id: str
    assertion_a_id: str
    assertion_b_id: str

    # Structural comparison
    same_attestation: bool = False
    same_proposition: bool = False
    same_evidence: bool = False
    same_semantics: bool = False
    same_rules: bool = False
    same_lifecycle: bool = False
    same_provenance: bool = False

    # Dimension-level agreement
    agreement_dimensions: dict[StateDimension, DimensionStatus] = field(default_factory=dict)
    disagreement_dimensions: dict[StateDimension, str] = field(default_factory=dict)

    # Classification
    disagreement_classification: DisagreementClass = DisagreementClass.AGREEMENT

    # Independence
    independence_relationship: IndependenceRelationship = IndependenceRelationship.UNKNOWN

    # Details
    details: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Epistemic Conflict
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EpistemicConflict:
    """Structured contradiction between verifiers.

    Produced when two verifiers produce incompatible results under
    compatible semantics. NOT resolved by majority vote.
    """
    conflict_id: str
    proposition_id: str

    # Assertions involved
    assertions: list[VerificationAssertion] = field(default_factory=list)

    # Common and divergent evidence
    common_evidence: list[str] = field(default_factory=list)
    divergent_evidence: list[str] = field(default_factory=list)

    # Semantic regime
    semantic_regime: str = "1.0.0"

    # Conflicting dimensions
    conflicting_dimensions: dict[StateDimension, str] = field(default_factory=dict)

    # Possible resolution paths
    possible_resolution_paths: list[str] = field(default_factory=list)

    # Status
    unresolved: bool = True

    # Provenance
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the conflict."""
        content = json.dumps({
            "conflict_id": self.conflict_id,
            "proposition_id": self.proposition_id,
            "assertion_ids": [a.assertion_id for a in self.assertions],
            "common_evidence": sorted(self.common_evidence),
            "divergent_evidence": sorted(self.divergent_evidence),
            "semantic_regime": self.semantic_regime,
            "conflicting_dimensions": {k.value: v for k, v in self.conflicting_dimensions.items()},
            "unresolved": self.unresolved,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Epistemic Consensus
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EpistemicConsensus:
    """Derived artifact representing the relationship between verifiers.

    NOT a scalar consensus_score. Instead a structural representation
    of agreement and disagreement.

    A consensus artifact must never simply contain:
        consensus = true

    It must contain the derivation basis for that conclusion.
    """
    consensus_id: str
    proposition_id: str

    # Assertion references
    assertion_refs: list[str] = field(default_factory=list)

    # Comparison references
    comparison_refs: list[str] = field(default_factory=list)

    # Dimension-level agreement
    agreement_dimensions: dict[StateDimension, DimensionStatus] = field(default_factory=dict)
    disagreement_dimensions: dict[StateDimension, str] = field(default_factory=dict)

    # Unresolved conflicts
    unresolved_conflicts: list[str] = field(default_factory=list)

    # Semantic regime
    semantic_regime: str = "1.0.0"

    # Independence evidence
    independence_evidence: dict[str, IndependenceRelationship] = field(default_factory=dict)

    # Provenance
    provenance_hash: str = ""
    derivation_hash: str = ""

    # Status
    has_consensus: bool = False
    consensus_basis: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the consensus."""
        content = json.dumps({
            "consensus_id": self.consensus_id,
            "proposition_id": self.proposition_id,
            "assertion_refs": sorted(self.assertion_refs),
            "comparison_refs": sorted(self.comparison_refs),
            "agreement_dimensions": {k.value: v.value for k, v in self.agreement_dimensions.items()},
            "unresolved_conflicts": sorted(self.unresolved_conflicts),
            "semantic_regime": self.semantic_regime,
            "has_consensus": self.has_consensus,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Consensus Builder
# ---------------------------------------------------------------------------


class ConsensusBuilder:
    """Builds consensus artifacts from verification assertions.

    The builder does NOT use majority voting. It classifies disagreement
    structurally and preserves uncertainty.
    """

    def __init__(self, semantic_regime: str = "1.0.0"):
        self.semantic_regime = semantic_regime

    def build_consensus(
        self,
        proposition_id: str,
        assertions: list[VerificationAssertion],
        comparisons: list[VerifierComparison],
    ) -> EpistemicConsensus:
        """Build a consensus artifact from assertions and comparisons."""
        # Collect dimension-level agreement from comparisons
        agreement_dimensions = {}
        disagreement_dimensions = {}

        for comparison in comparisons:
            for dim, status in comparison.agreement_dimensions.items():
                if dim not in agreement_dimensions:
                    agreement_dimensions[dim] = status
            for dim, detail in comparison.disagreement_dimensions.items():
                disagreement_dimensions[dim] = detail

        # Collect unresolved conflicts from comparisons
        unresolved_conflicts = [
            c.comparison_id for c in comparisons
            if c.disagreement_classification != DisagreementClass.AGREEMENT
        ]

        # Determine if consensus exists
        if len(assertions) == 1 and len(comparisons) == 0:
            # Single verifier is trivially consensus
            has_consensus = True
        else:
            has_consensus = (
                len(unresolved_conflicts) == 0
                and len(comparisons) > 0
                and all(c.disagreement_classification == DisagreementClass.AGREEMENT for c in comparisons)
            )

        # Build basis
        if has_consensus:
            basis = f"Agreement on {len(agreement_dimensions)} dimensions across {len(assertions)} verifiers"
        elif len(comparisons) == 0:
            basis = f"No comparisons available for {len(assertions)} verifiers"
        else:
            basis = f"Disagreement on {len(disagreement_dimensions)} dimensions, {len(unresolved_conflicts)} unresolved conflicts"

        consensus = EpistemicConsensus(
            consensus_id=f"consensus_{proposition_id}_{self._hash_list([a.assertion_id for a in assertions])}",
            proposition_id=proposition_id,
            assertion_refs=[a.assertion_id for a in assertions],
            comparison_refs=[c.comparison_id for c in comparisons],
            agreement_dimensions=agreement_dimensions,
            disagreement_dimensions=disagreement_dimensions,
            unresolved_conflicts=unresolved_conflicts,
            semantic_regime=self.semantic_regime,
            has_consensus=has_consensus,
            consensus_basis=basis,
        )

        # Set hashes
        consensus = EpistemicConsensus(
            **{**dataclasses.asdict(consensus),
               "provenance_hash": consensus.compute_hash(),
               "derivation_hash": consensus.compute_hash()}
        )

        return consensus

    def _hash_list(self, items: list[str]) -> str:
        """Hash a list of items."""
        content = json.dumps(sorted(items), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Verifier Comparison Engine
# ---------------------------------------------------------------------------


class VerifierComparisonEngine:
    """Deterministic engine for comparing verification assertions."""

    def compare(
        self,
        assertion_a: VerificationAssertion,
        assertion_b: VerificationAssertion,
    ) -> VerifierComparison:
        """Compare two verification assertions structurally."""
        # Check structural equality
        same_attestation = assertion_a.attestation_hash == assertion_b.attestation_hash
        same_evidence = set(assertion_a.evidence_refs) == set(assertion_b.evidence_refs)
        same_semantics = assertion_a.semantic_rule_version == assertion_b.semantic_rule_version
        same_rules = (
            assertion_a.verifier_identity.epistemic_rule_version
            == assertion_b.verifier_identity.epistemic_rule_version
        )
        same_lifecycle = (
            assertion_a.verifier_identity.lifecycle_rules_version
            == assertion_b.verifier_identity.lifecycle_rules_version
        )
        same_provenance = set(assertion_a.provenance_refs) == set(assertion_b.provenance_refs)

        # Determine independence relationship
        independence = self._determine_independence(assertion_a, assertion_b)

        # Compare dimensions
        agreement_dimensions = {}
        disagreement_dimensions = {}

        all_dims = set(assertion_a.verified_dimensions.keys()) | set(assertion_b.verified_dimensions.keys())
        all_dims |= set(assertion_a.failed_dimensions.keys()) | set(assertion_b.failed_dimensions.keys())
        all_dims |= set(assertion_a.unresolved_dimensions.keys()) | set(assertion_b.unresolved_dimensions.keys())

        for dim in all_dims:
            a_status = assertion_a.verified_dimensions.get(dim)
            b_status = assertion_b.verified_dimensions.get(dim)

            if a_status and b_status and a_status == b_status:
                agreement_dimensions[dim] = a_status
            elif a_status and not b_status:
                disagreement_dimensions[dim] = f"A={a_status.value}, B=other"
            elif not a_status and b_status:
                disagreement_dimensions[dim] = f"A=other, B={b_status.value}"
            else:
                disagreement_dimensions[dim] = "both_different"

        # Classify disagreement
        classification = self._classify_disagreement(
            same_attestation=same_attestation,
            same_evidence=same_evidence,
            same_semantics=same_semantics,
            same_rules=same_rules,
            same_lifecycle=same_lifecycle,
            same_provenance=same_provenance,
            agreement_dimensions=agreement_dimensions,
            disagreement_dimensions=disagreement_dimensions,
        )

        details = []
        if not same_attestation:
            details.append("Different attestations")
        if not same_evidence:
            details.append("Different evidence sets")
        if not same_semantics:
            details.append("Different semantic rule versions")
        if not same_rules:
            details.append("Different epistemic rule versions")
        if not same_lifecycle:
            details.append("Different lifecycle rules")
        if not same_provenance:
            details.append("Different provenance")

        return VerifierComparison(
            comparison_id=f"comp_{assertion_a.assertion_id}_{assertion_b.assertion_id}",
            assertion_a_id=assertion_a.assertion_id,
            assertion_b_id=assertion_b.assertion_id,
            same_attestation=same_attestation,
            same_proposition=True,  # Same proposition if same attestation
            same_evidence=same_evidence,
            same_semantics=same_semantics,
            same_rules=same_rules,
            same_lifecycle=same_lifecycle,
            same_provenance=same_provenance,
            agreement_dimensions=agreement_dimensions,
            disagreement_dimensions=disagreement_dimensions,
            disagreement_classification=classification,
            independence_relationship=independence,
            details=details,
        )

    def _determine_independence(
        self,
        a: VerificationAssertion,
        b: VerificationAssertion,
    ) -> IndependenceRelationship:
        """Determine the independence relationship between two verifiers."""
        id_a = a.verifier_identity
        id_b = id_b = b.verifier_identity

        # Same verifier
        if id_a.verifier_id == id_b.verifier_id:
            return IndependenceRelationship.DERIVED_FROM

        # Same implementation
        if id_a.implementation_id == id_b.implementation_id:
            return IndependenceRelationship.SHARES_IMPLEMENTATION

        # Same rule engine
        if id_a.epistemic_rule_version == id_b.epistemic_rule_version:
            return IndependenceRelationship.SHARES_RULE_ENGINE

        # Same evidence
        if set(a.evidence_refs) == set(b.evidence_refs):
            return IndependenceRelationship.SHARES_EVIDENCE

        # Otherwise unknown (not proven independent)
        return IndependenceRelationship.UNKNOWN

    def _classify_disagreement(
        self,
        same_attestation: bool,
        same_evidence: bool,
        same_semantics: bool,
        same_rules: bool,
        same_lifecycle: bool,
        same_provenance: bool,
        agreement_dimensions: dict,
        disagreement_dimensions: dict,
    ) -> DisagreementClass:
        """Classify the disagreement type."""
        if not same_attestation:
            return DisagreementClass.UNRESOLVED_VERIFICATION_CONFLICT

        if not same_evidence:
            return DisagreementClass.EVIDENCE_DIVERGENCE

        if not same_provenance:
            return DisagreementClass.PROVENANCE_DIVERGENCE

        if not same_semantics:
            return DisagreementClass.SEMANTIC_DIVERGENCE

        if not same_rules:
            return DisagreementClass.RULE_VERSION_DIVERGENCE

        if not same_lifecycle:
            return DisagreementClass.LIFECYCLE_DIVERGENCE

        if disagreement_dimensions:
            return DisagreementClass.RECONSTRUCTION_DIVERGENCE

        if agreement_dimensions and not disagreement_dimensions:
            return DisagreementClass.AGREEMENT

        return DisagreementClass.UNRESOLVED_VERIFICATION_CONFLICT


# ---------------------------------------------------------------------------
# Multi-Verifier Orchestrator
# ---------------------------------------------------------------------------


class MultiVerifierOrchestrator:
    """Orchestrates multiple verifiers and produces consensus artifacts."""

    def __init__(self):
        self.verifiers: dict[str, EpistemicVerifier] = {}
        self.identities: dict[str, VerifierIdentity] = {}
        self.assertions: list[VerificationAssertion] = []
        self.comparison_engine = VerifierComparisonEngine()
        self.consensus_builder = ConsensusBuilder()

    def register_verifier(
        self,
        verifier_id: str,
        identity: VerifierIdentity,
        verifier: EpistemicVerifier,
    ) -> None:
        """Register a verifier with its identity."""
        self.verifiers[verifier_id] = verifier
        self.identities[verifier_id] = identity

    def run_verification(
        self,
        attestation: EpistemicAttestation,
        artifacts: dict,
    ) -> list[VerificationAssertion]:
        """Run all registered verifiers and produce assertions."""
        assertions = []
        for verifier_id, verifier in self.verifiers.items():
            identity = self.identities[verifier_id]
            result = verifier.verify_attestation(attestation, artifacts)

            # Convert result to assertion
            assertion = self._result_to_assertion(identity, result, attestation, artifacts)
            assertions.append(assertion)

        self.assertions.extend(assertions)
        return assertions

    def compare_assertions(
        self,
        assertions: list[VerificationAssertion],
    ) -> list[VerifierComparison]:
        """Compare all pairs of assertions."""
        comparisons = []
        for i in range(len(assertions)):
            for j in range(i + 1, len(assertions)):
                comparison = self.comparison_engine.compare(
                    assertions[i], assertions[j]
                )
                comparisons.append(comparison)
        return comparisons

    def build_consensus(
        self,
        proposition_id: str,
        assertions: list[VerificationAssertion],
        comparisons: list[VerifierComparison],
    ) -> EpistemicConsensus:
        """Build consensus from assertions and comparisons."""
        return self.consensus_builder.build_consensus(
            proposition_id, assertions, comparisons
        )

    def _result_to_assertion(
        self,
        identity: VerifierIdentity,
        result: VerificationResult,
        attestation: EpistemicAttestation,
        artifacts: dict,
    ) -> VerificationAssertion:
        """Convert a verification result to an assertion."""
        # Extract dimension states from artifacts
        state = artifacts.get("state")
        verified_dimensions = {}
        failed_dimensions = {}
        unresolved_dimensions = {}

        if state and hasattr(state, 'dimension_states'):
            for dim, dim_state in state.dimension_states.items():
                if result.valid:
                    verified_dimensions[dim] = dim_state.status
                elif result.status == VerificationStatus.SEMANTICALLY_INVALID:
                    failed_dimensions[dim] = result.status.value
                else:
                    unresolved_dimensions[dim] = result.status.value

        assertion = VerificationAssertion(
            assertion_id=f"assert_{identity.verifier_id}_{attestation.attestation_id}",
            verifier_identity=identity,
            attestation_hash=attestation.attestation_hash,
            verified_dimensions=verified_dimensions,
            failed_dimensions=failed_dimensions,
            unresolved_dimensions=unresolved_dimensions,
            verification_trace_hash=_hash_trace(result.trace) if result.trace else "",
            semantic_rule_version=identity.epistemic_rule_version,
            evidence_refs=attestation.evidence_hashes,
            provenance_refs=[attestation.provenance_root],
            overall_status=result.status,
        )

        # Set result hash - manually reconstruct to avoid dataclasses.asdict
        # recursively converting nested frozen dataclasses to dicts
        assertion = VerificationAssertion(
            assertion_id=assertion.assertion_id,
            verifier_identity=assertion.verifier_identity,
            attestation_hash=assertion.attestation_hash,
            verified_dimensions=assertion.verified_dimensions,
            failed_dimensions=assertion.failed_dimensions,
            unresolved_dimensions=assertion.unresolved_dimensions,
            verification_trace_hash=assertion.verification_trace_hash,
            semantic_rule_version=assertion.semantic_rule_version,
            evidence_refs=assertion.evidence_refs,
            provenance_refs=assertion.provenance_refs,
            overall_status=assertion.overall_status,
            result_hash=assertion.compute_hash(),
        )

        return assertion


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def _hash_trace(trace: VerificationTrace) -> str:
    """Hash a verification trace."""
    content = json.dumps({
        "trace_id": trace.trace_id,
        "attestation_id": trace.attestation_id,
        "steps": trace.steps,
        "final_status": trace.final_status.value,
    }, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def create_verifier_identity(
    verifier_id: str,
    implementation_id: str,
    **kwargs,
) -> VerifierIdentity:
    """Create a verifier identity."""
    return VerifierIdentity(
        verifier_id=verifier_id,
        implementation_id=implementation_id,
        **kwargs,
    )


def compare_verifier_assertions(
    assertion_a: VerificationAssertion,
    assertion_b: VerificationAssertion,
) -> VerifierComparison:
    """Compare two verification assertions."""
    engine = VerifierComparisonEngine()
    return engine.compare(assertion_a, assertion_b)


def build_epistemic_consensus(
    proposition_id: str,
    assertions: list[VerificationAssertion],
    comparisons: list[VerifierComparison],
) -> EpistemicConsensus:
    """Build epistemic consensus."""
    builder = ConsensusBuilder()
    return builder.build_consensus(proposition_id, assertions, comparisons)
