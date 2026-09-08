"""Tests for Epistemic Verification module."""

from __future__ import annotations

import pytest

from sas.quant.experiment.epistemic_verification import (
    VerificationStatus,
    IntegrityCheck,
    EpistemicAttestation,
    VerificationTrace,
    VerificationResult,
    EpistemicVerifier,
    build_attestation,
    verify_epistemic_state,
)
from sas.quant.experiment.epistemic_state import (
    EpistemicStatus,
    StateDimension,
    DimensionStatus,
    EpistemicState,
    TransitionType,
    EpistemicTransition,
    EpistemicStateMachine,
    create_initial_state,
    apply_evidence,
)
from sas.quant.experiment.evidence_structure import (
    StructuredEvidenceBundle,
)
from sas.quant.experiment.typed_propositions import (
    InterventionType,
    PropositionType,
    TypedProposition,
)


# ---------------------------------------------------------------------------
# Test: Verification Status
# ---------------------------------------------------------------------------


class TestVerificationStatus:
    def test_all_statuses_present(self):
        statuses = list(VerificationStatus)
        assert len(statuses) == 8
        assert VerificationStatus.VALID in statuses
        assert VerificationStatus.INVALID in statuses
        assert VerificationStatus.FORGED in statuses
        assert VerificationStatus.SEMANTICALLY_INVALID in statuses


# ---------------------------------------------------------------------------
# Test: Epistemic Attestation
# ---------------------------------------------------------------------------


class TestEpistemicAttestation:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_compute_hash(self):
        prop = self._create_proposition()
        state = create_initial_state(prop)

        attestation = EpistemicAttestation(
            attestation_id="attestation_1",
            proposition_hash="hash1",
            state_hash=state.provenance_hash,
            transition_hash="hash2",
        )

        hash1 = attestation.compute_hash()
        hash2 = attestation.compute_hash()
        assert hash1 == hash2
        assert len(hash1) == 16

    def test_hash_deterministic(self):
        prop = self._create_proposition()
        state = create_initial_state(prop)

        attestation1 = EpistemicAttestation(
            attestation_id="attestation_1",
            proposition_hash="hash1",
            state_hash=state.provenance_hash,
            transition_hash="hash2",
            evidence_hashes=["e1", "e2"],
        )

        attestation2 = EpistemicAttestation(
            attestation_id="attestation_1",
            proposition_hash="hash1",
            state_hash=state.provenance_hash,
            transition_hash="hash2",
            evidence_hashes=["e1", "e2"],
        )

        assert attestation1.compute_hash() == attestation2.compute_hash()


# ---------------------------------------------------------------------------
# Test: Verification Trace
# ---------------------------------------------------------------------------


class TestVerificationTrace:
    def test_add_step(self):
        trace = VerificationTrace(
            trace_id="trace_1",
            attestation_id="attestation_1",
        )

        trace.add_step("proposition", True, "Hash verified")
        trace.add_step("evidence", False, "Hash mismatch")

        assert len(trace.steps) == 2
        assert trace.steps[0]["passed"] is True
        assert trace.steps[1]["passed"] is False

    def test_explain(self):
        trace = VerificationTrace(
            trace_id="trace_1",
            attestation_id="attestation_1",
        )

        trace.add_step("proposition", True, "Hash verified")
        explanation = trace.explain()
        assert "trace_1" in explanation
        assert "proposition" in explanation


# ---------------------------------------------------------------------------
# Test: Epistemic Verifier
# ---------------------------------------------------------------------------


class TestEpistemicVerifier:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def _create_valid_state_with_evidence(self):
        """Create a valid state with evidence for testing."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        initial_state = machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=i + 1,
            )
            for i in range(5)
        ]

        transition, new_state = machine.apply_evidence(evidence)
        return prop, machine, initial_state, transition, new_state, evidence

    def test_verify_valid_state(self):
        """Test that a valid state passes verification."""
        prop, machine, initial_state, transition, new_state, evidence = self._create_valid_state_with_evidence()

        attestation = build_attestation(prop, new_state, transition, evidence)

        artifacts = {
            "proposition": prop,
            "state": new_state,
            "transition": transition,
            "previous_state": initial_state,
            "evidence": evidence,
        }

        verifier = EpistemicVerifier()
        result = verifier.verify_attestation(attestation, artifacts)

        assert result.valid
        assert result.status == VerificationStatus.VALID
        assert result.proposition_valid
        assert result.evidence_valid
        assert result.provenance_valid

    def test_verify_forged_state(self):
        """Test that a forged state fails verification."""
        prop, machine, initial_state, transition, new_state, evidence = self._create_valid_state_with_evidence()

        # Create attestation with wrong state hash
        attestation = EpistemicAttestation(
            attestation_id="attestation_1",
            proposition_hash="wrong_hash",
            state_hash="wrong_hash",
            transition_hash=transition.provenance_hash,
        )

        artifacts = {
            "proposition": prop,
            "state": new_state,
            "transition": transition,
            "previous_state": initial_state,
            "evidence": evidence,
        }

        verifier = EpistemicVerifier()
        result = verifier.verify_attestation(attestation, artifacts)

        assert not result.valid

    def test_verify_modified_evidence(self):
        """Test that modified evidence fails verification."""
        prop, machine, initial_state, transition, new_state, evidence = self._create_valid_state_with_evidence()

        attestation = build_attestation(prop, new_state, transition, evidence)

        # Modify evidence
        modified_evidence = [
            StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.9,  # Changed from 0.8
                description="Mechanism evidence",
                seed=i + 1,
            )
            for i in range(5)
        ]

        artifacts = {
            "proposition": prop,
            "state": new_state,
            "transition": transition,
            "previous_state": initial_state,
            "evidence": modified_evidence,
        }

        verifier = EpistemicVerifier()
        result = verifier.verify_attestation(attestation, artifacts)

        assert not result.valid

    def test_verify_missing_evidence(self):
        """Test that missing evidence fails verification."""
        prop, machine, initial_state, transition, new_state, evidence = self._create_valid_state_with_evidence()

        attestation = build_attestation(prop, new_state, transition, evidence)

        # Remove some evidence
        artifacts = {
            "proposition": prop,
            "state": new_state,
            "transition": transition,
            "previous_state": initial_state,
            "evidence": evidence[:2],  # Only 2 of 5
        }

        verifier = EpistemicVerifier()
        result = verifier.verify_attestation(attestation, artifacts)

        assert not result.valid

    def test_verify_wrong_intervention(self):
        """Test that wrong intervention type fails verification."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        initial_state = machine.create_initial_state()

        # Evidence with wrong intervention type
        evidence = [
            StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.FEATURE_ABLATION,
                target="signal",
                effect_size=0.8,
                description="Wrong type",
                seed=i + 1,
            )
            for i in range(5)
        ]

        transition, new_state = machine.apply_evidence(evidence)
        attestation = build_attestation(prop, new_state, transition, evidence)

        artifacts = {
            "proposition": prop,
            "state": new_state,
            "transition": transition,
            "previous_state": initial_state,
            "evidence": evidence,
        }

        verifier = EpistemicVerifier()
        result = verifier.verify_attestation(attestation, artifacts)

        # Should fail because wrong intervention type
        assert not result.valid

    def test_verification_trace_provided(self):
        """Test that verification produces a trace."""
        prop, machine, initial_state, transition, new_state, evidence = self._create_valid_state_with_evidence()

        attestation = build_attestation(prop, new_state, transition, evidence)

        artifacts = {
            "proposition": prop,
            "state": new_state,
            "transition": transition,
            "previous_state": initial_state,
            "evidence": evidence,
        }

        verifier = EpistemicVerifier()
        result = verifier.verify_attestation(attestation, artifacts)

        assert result.trace is not None
        assert len(result.trace.steps) > 0


# ---------------------------------------------------------------------------
# Test: State Forgery Detection
# ---------------------------------------------------------------------------


class TestStateForgeryDetection:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_modified_status_detected(self):
        """Modified status should be detected."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        initial_state = machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=1,
            )
        ]

        transition, new_state = machine.apply_evidence(evidence)

        # Create a forged state with modified status
        forged_state = EpistemicState(
            state_id=new_state.state_id,
            proposition_id=new_state.proposition_id,
            proposition_type=new_state.proposition_type,
            status=EpistemicStatus.SUPPORTED,  # Forged
            dimension_states=new_state.dimension_states,
            established_dimensions=new_state.established_dimensions,
            unresolved_dimensions=new_state.unresolved_dimensions,
            epistemic_gaps=new_state.epistemic_gaps,
            evidence_refs=new_state.evidence_refs,
            experiment_refs=new_state.experiment_refs,
            intervention_refs=new_state.intervention_refs,
            authority_scope=new_state.authority_scope,
            blocking_alternatives=new_state.blocking_alternatives,
            parent_state_id=new_state.parent_state_id,
            transition_id=new_state.transition_id,
            provenance_hash="forged_hash",
        )

        attestation = build_attestation(prop, forged_state, transition, evidence)

        artifacts = {
            "proposition": prop,
            "state": forged_state,
            "transition": transition,
            "previous_state": initial_state,
            "evidence": evidence,
        }

        verifier = EpistemicVerifier()
        result = verifier.verify_attestation(attestation, artifacts)

        assert not result.valid

    def test_modified_evidence_refs_detected(self):
        """Modified evidence references should be detected."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        initial_state = machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=1,
            )
        ]

        transition, new_state = machine.apply_evidence(evidence)

        # Create a forged state with extra evidence refs
        forged_state = EpistemicState(
            state_id=new_state.state_id,
            proposition_id=new_state.proposition_id,
            proposition_type=new_state.proposition_type,
            status=new_state.status,
            dimension_states=new_state.dimension_states,
            established_dimensions=new_state.established_dimensions,
            unresolved_dimensions=new_state.unresolved_dimensions,
            epistemic_gaps=new_state.epistemic_gaps,
            evidence_refs=new_state.evidence_refs + ["forged_evidence"],
            experiment_refs=new_state.experiment_refs,
            intervention_refs=new_state.intervention_refs,
            authority_scope=new_state.authority_scope,
            blocking_alternatives=new_state.blocking_alternatives,
            parent_state_id=new_state.parent_state_id,
            transition_id=new_state.transition_id,
            provenance_hash=new_state.provenance_hash,
        )

        attestation = build_attestation(prop, forged_state, transition, evidence)

        artifacts = {
            "proposition": prop,
            "state": forged_state,
            "transition": transition,
            "previous_state": initial_state,
            "evidence": evidence,
        }

        verifier = EpistemicVerifier()
        result = verifier.verify_attestation(attestation, artifacts)

        assert not result.valid


# ---------------------------------------------------------------------------
# Test: Transition Forgery Detection
# ---------------------------------------------------------------------------


class TestTransitionForgeryDetection:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_unauthorized_authority_increase(self):
        """Unauthorized authority increase should be detected."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        initial_state = machine.create_initial_state()

        # Evidence that doesn't justify authority increase
        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.FEATURE_ABLATION,
                target="signal",
                effect_size=0.8,
                description="Wrong type",
                seed=1,
            )
        ]

        transition, new_state = machine.apply_evidence(evidence)

        # Create a forged transition claiming authority increase
        forged_transition = EpistemicTransition(
            transition_id=transition.transition_id,
            proposition_id=transition.proposition_id,
            previous_state_id=transition.previous_state_id,
            resulting_state_id=transition.resulting_state_id,
            transition_type=TransitionType.AUTHORITY_INCREASED,
            authority_added={"mechanism": "forged authority"},
        )

        attestation = build_attestation(prop, new_state, forged_transition, evidence)

        artifacts = {
            "proposition": prop,
            "state": new_state,
            "transition": forged_transition,
            "previous_state": initial_state,
            "evidence": evidence,
        }

        verifier = EpistemicVerifier()
        result = verifier.verify_attestation(attestation, artifacts)

        assert not result.valid


# ---------------------------------------------------------------------------
# Test: Provenance Substitution Detection
# ---------------------------------------------------------------------------


class TestProvenanceSubstitution:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_evidence_substitution_detected(self):
        """Evidence substitution should be detected."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        initial_state = machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=1,
            )
        ]

        transition, new_state = machine.apply_evidence(evidence)
        attestation = build_attestation(prop, new_state, transition, evidence)

        # Substitute different evidence
        substituted_evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.5,  # Different effect
                description="Substituted evidence",
                seed=2,  # Different seed
            )
        ]

        artifacts = {
            "proposition": prop,
            "state": new_state,
            "transition": transition,
            "previous_state": initial_state,
            "evidence": substituted_evidence,
        }

        verifier = EpistemicVerifier()
        result = verifier.verify_attestation(attestation, artifacts)

        assert not result.valid


# ---------------------------------------------------------------------------
# Test: Duplicate Evidence Detection
# ---------------------------------------------------------------------------


class TestDuplicateEvidence:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_duplicate_evidence_same_id(self):
        """Duplicate evidence (same ID) should be detected."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        initial_state = machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=1,
            )
        ]

        transition, new_state = machine.apply_evidence(evidence)
        attestation = build_attestation(prop, new_state, transition, evidence)

        # Submit same evidence twice
        duplicate_evidence = evidence + evidence

        artifacts = {
            "proposition": prop,
            "state": new_state,
            "transition": transition,
            "previous_state": initial_state,
            "evidence": duplicate_evidence,
        }

        verifier = EpistemicVerifier()
        result = verifier.verify_attestation(attestation, artifacts)

        assert not result.valid


# ---------------------------------------------------------------------------
# Test: Verification Result Explanation
# ---------------------------------------------------------------------------


class TestVerificationResult:
    def test_explain(self):
        result = VerificationResult(
            valid=True,
            status=VerificationStatus.VALID,
            proposition_valid=True,
            evidence_valid=True,
        )

        explanation = result.explain()
        assert "Valid: True" in explanation
        assert "valid" in explanation

    def test_explain_with_discrepancies(self):
        result = VerificationResult(
            valid=False,
            status=VerificationStatus.FORGED,
            discrepancies=["Hash mismatch", "Missing evidence"],
        )

        explanation = result.explain()
        assert "Hash mismatch" in explanation
        assert "Missing evidence" in explanation


# ---------------------------------------------------------------------------
# Test: Convenience Function
# ---------------------------------------------------------------------------


class TestVerifyEpistemicState:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_verify_epistemic_state_convenience(self):
        """Test the convenience function."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        initial_state = machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=i + 1,
            )
            for i in range(5)
        ]

        transition, new_state = machine.apply_evidence(evidence)
        attestation = build_attestation(prop, new_state, transition, evidence)

        result = verify_epistemic_state(
            attestation, prop, new_state, transition, initial_state, evidence
        )

        assert result.valid
        assert result.status == VerificationStatus.VALID


# ---------------------------------------------------------------------------
# Test: Minimal Verification
# ---------------------------------------------------------------------------


class TestMinimalVerification:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_state_only_insufficient(self):
        """State alone should not be sufficient for verification."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        initial_state = machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=1,
            )
        ]

        transition, new_state = machine.apply_evidence(evidence)
        attestation = build_attestation(prop, new_state, transition, evidence)

        # Only provide state, no evidence
        artifacts = {
            "proposition": prop,
            "state": new_state,
        }

        verifier = EpistemicVerifier()
        result = verifier.verify_attestation(attestation, artifacts)

        assert not result.valid


# ---------------------------------------------------------------------------
# Test: Attestation Builder
# ---------------------------------------------------------------------------


class TestBuildAttestation:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_build_attestation(self):
        """Test building an attestation."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        initial_state = machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=1,
            )
        ]

        transition, new_state = machine.apply_evidence(evidence)
        attestation = build_attestation(prop, new_state, transition, evidence)

        assert attestation.attestation_id == f"attestation_{new_state.state_id}"
        assert len(attestation.evidence_hashes) == 1
        assert attestation.attestation_hash == attestation.compute_hash()

    def test_attestation_hash_set(self):
        """Test that attestation hash is properly set."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        initial_state = machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=1,
            )
        ]

        transition, new_state = machine.apply_evidence(evidence)
        attestation = build_attestation(prop, new_state, transition, evidence)

        assert len(attestation.attestation_hash) == 16


# ---------------------------------------------------------------------------
# Test: Integrity vs Semantic Validity
# ---------------------------------------------------------------------------


class TestIntegrityVsSemanticValidity:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_integrity_without_semantic_validity(self):
        """Test that integrity does not imply semantic validity."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        initial_state = machine.create_initial_state()

        # Evidence with wrong intervention type (integrity OK, semantics wrong)
        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.FEATURE_ABLATION,
                target="signal",
                effect_size=0.8,
                description="Wrong type",
                seed=1,
            )
        ]

        transition, new_state = machine.apply_evidence(evidence)
        attestation = build_attestation(prop, new_state, transition, evidence)

        artifacts = {
            "proposition": prop,
            "state": new_state,
            "transition": transition,
            "previous_state": initial_state,
            "evidence": evidence,
        }

        verifier = EpistemicVerifier()
        result = verifier.verify_attestation(attestation, artifacts)

        # Integrity may pass (hashes match), but semantic validity should fail
        assert not result.valid
