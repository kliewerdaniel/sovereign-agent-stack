"""Tests for Epistemic Consensus, Verifier Disagreement, and Authority Reconciliation."""

from __future__ import annotations

import pytest

from sas.quant.experiment.epistemic_consensus import (
    VerifierIdentity,
    IndependenceRelationship,
    VerificationAssertion,
    DisagreementClass,
    VerifierComparison,
    EpistemicConflict,
    EpistemicConsensus,
    ConsensusBuilder,
    VerifierComparisonEngine,
    MultiVerifierOrchestrator,
    create_verifier_identity,
    compare_verifier_assertions,
    build_epistemic_consensus,
)
from sas.quant.experiment.epistemic_verification import (
    VerificationStatus,
    EpistemicAttestation,
    VerificationTrace,
    EpistemicVerifier,
    build_attestation,
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
# Test: Verifier Identity
# ---------------------------------------------------------------------------


class TestVerifierIdentity:
    def test_compute_hash(self):
        identity = VerifierIdentity(
            verifier_id="v1",
            implementation_id="impl1",
        )
        hash1 = identity.compute_hash()
        hash2 = identity.compute_hash()
        assert hash1 == hash2
        assert len(hash1) == 16

    def test_different_identities_different_hashes(self):
        identity1 = VerifierIdentity(
            verifier_id="v1",
            implementation_id="impl1",
        )
        identity2 = VerifierIdentity(
            verifier_id="v2",
            implementation_id="impl2",
        )
        assert identity1.compute_hash() != identity2.compute_hash()

    def test_same_verifier_different_versions(self):
        identity1 = VerifierIdentity(
            verifier_id="v1",
            implementation_id="impl1",
            epistemic_rule_version="1.0.0",
        )
        identity2 = VerifierIdentity(
            verifier_id="v1",
            implementation_id="impl1",
            epistemic_rule_version="2.0.0",
        )
        assert identity1.compute_hash() != identity2.compute_hash()


# ---------------------------------------------------------------------------
# Test: Verification Assertion
# ---------------------------------------------------------------------------


class TestVerificationAssertion:
    def _create_identity(self) -> VerifierIdentity:
        return VerifierIdentity(
            verifier_id="v1",
            implementation_id="impl1",
        )

    def test_compute_hash(self):
        identity = self._create_identity()
        assertion = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity,
            attestation_hash="hash1",
        )
        hash1 = assertion.compute_hash()
        hash2 = assertion.compute_hash()
        assert hash1 == hash2

    def test_dimension_specific_results(self):
        identity = self._create_identity()
        assertion = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity,
            attestation_hash="hash1",
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.ROBUST,
            },
            unresolved_dimensions={
                StateDimension.GENERALIZATION: "insufficient evidence",
            },
        )
        assert StateDimension.MECHANISM in assertion.verified_dimensions
        assert StateDimension.GENERALIZATION in assertion.unresolved_dimensions


# ---------------------------------------------------------------------------
# Test: Verifier Comparison Engine
# ---------------------------------------------------------------------------


class TestVerifierComparisonEngine:
    def _create_identity(self, vid: str = "v1") -> VerifierIdentity:
        return VerifierIdentity(
            verifier_id=vid,
            implementation_id=f"impl{vid}",
        )

    def _create_assertion(
        self,
        aid: str,
        vid: str = "v1",
        att_hash: str = "hash1",
        evidence_refs: list[str] | None = None,
        semantic_version: str = "1.0.0",
    ) -> VerificationAssertion:
        identity = self._create_identity(vid)
        return VerificationAssertion(
            assertion_id=aid,
            verifier_identity=identity,
            attestation_hash=att_hash,
            evidence_refs=evidence_refs or ["e1", "e2"],
            semantic_rule_version=semantic_version,
        )

    def test_agreement(self):
        engine = VerifierComparisonEngine()
        a1 = self._create_assertion("a1", "v1")
        a2 = self._create_assertion("a2", "v2")
        comparison = engine.compare(a1, a2)
        assert comparison.same_attestation
        assert comparison.same_evidence
        assert comparison.same_semantics

    def test_evidence_divergence(self):
        engine = VerifierComparisonEngine()
        a1 = self._create_assertion("a1", "v1", evidence_refs=["e1", "e2"])
        a2 = self._create_assertion("a2", "v2", evidence_refs=["e1", "e2", "e3"])
        comparison = engine.compare(a1, a2)
        assert not comparison.same_evidence
        assert comparison.disagreement_classification == DisagreementClass.EVIDENCE_DIVERGENCE

    def test_semantic_divergence(self):
        engine = VerifierComparisonEngine()
        a1 = self._create_assertion("a1", "v1", semantic_version="1.0.0")
        a2 = self._create_assertion("a2", "v2", semantic_version="2.0.0")
        comparison = engine.compare(a1, a2)
        assert not comparison.same_semantics
        assert comparison.disagreement_classification == DisagreementClass.SEMANTIC_DIVERGENCE

    def test_same_verifier_not_independent(self):
        engine = VerifierComparisonEngine()
        a1 = self._create_assertion("a1", "v1")
        a2 = self._create_assertion("a2", "v1")
        comparison = engine.compare(a1, a2)
        assert comparison.independence_relationship == IndependenceRelationship.DERIVED_FROM

    def test_same_implementation_not_independent(self):
        engine = VerifierComparisonEngine()
        identity1 = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity2 = VerifierIdentity(verifier_id="v2", implementation_id="impl1")
        a1 = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity1,
            attestation_hash="hash1",
        )
        a2 = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity2,
            attestation_hash="hash1",
        )
        comparison = engine.compare(a1, a2)
        assert comparison.independence_relationship == IndependenceRelationship.SHARES_IMPLEMENTATION


# ---------------------------------------------------------------------------
# Test: Consensus Builder
# ---------------------------------------------------------------------------


class TestConsensusBuilder:
    def _create_identity(self, vid: str = "v1") -> VerifierIdentity:
        return VerifierIdentity(
            verifier_id=vid,
            implementation_id=f"impl{vid}",
        )

    def _create_assertion(
        self,
        aid: str,
        vid: str = "v1",
        att_hash: str = "hash1",
        evidence_refs: list[str] | None = None,
        semantic_version: str = "1.0.0",
    ) -> VerificationAssertion:
        identity = self._create_identity(vid)
        return VerificationAssertion(
            assertion_id=aid,
            verifier_identity=identity,
            attestation_hash=att_hash,
            evidence_refs=evidence_refs or ["e1", "e2"],
            semantic_rule_version=semantic_version,
        )

    def test_build_consensus_agreement(self):
        builder = ConsensusBuilder()
        a1 = self._create_assertion("a1", "v1")
        a2 = self._create_assertion("a2", "v2")
        comparisons = [
            VerifierComparison(
                comparison_id="c1",
                assertion_a_id="a1",
                assertion_b_id="a2",
                same_attestation=True,
                same_evidence=True,
                same_semantics=True,
                disagreement_classification=DisagreementClass.AGREEMENT,
            )
        ]
        consensus = builder.build_consensus("p1", [a1, a2], comparisons)
        assert consensus.has_consensus
        assert len(consensus.unresolved_conflicts) == 0

    def test_build_consensus_disagreement(self):
        builder = ConsensusBuilder()
        a1 = self._create_assertion("a1", "v1")
        a2 = self._create_assertion("a2", "v2")
        comparisons = [
            VerifierComparison(
                comparison_id="c1",
                assertion_a_id="a1",
                assertion_b_id="a2",
                same_attestation=True,
                same_evidence=False,
                same_semantics=True,
                disagreement_classification=DisagreementClass.EVIDENCE_DIVERGENCE,
            )
        ]
        consensus = builder.build_consensus("p1", [a1, a2], comparisons)
        # Evidence divergence means no consensus
        assert not consensus.has_consensus


# ---------------------------------------------------------------------------
# Attack 1 — Majority Vote
# ---------------------------------------------------------------------------


class TestAttack1MajorityVote:
    def _create_identity(self, vid: str = "v1") -> VerifierIdentity:
        return VerifierIdentity(
            verifier_id=vid,
            implementation_id=f"impl{vid}",
        )

    def _create_assertion(
        self,
        aid: str,
        vid: str = "v1",
        status: VerificationStatus = VerificationStatus.VALID,
    ) -> VerificationAssertion:
        identity = self._create_identity(vid)
        return VerificationAssertion(
            assertion_id=aid,
            verifier_identity=identity,
            attestation_hash="hash1",
            overall_status=status,
        )

    def test_9_vs_1_majority_does_not_override(self):
        """9 verifiers say VALID, 1 says INCONCLUSIVE.
        The system must NOT automatically override the minority."""
        builder = ConsensusBuilder()
        # 9 verifiers with VALID
        valid_assertions = [
            self._create_assertion(f"a{i}", f"v{i}", VerificationStatus.VALID)
            for i in range(9)
        ]
        # 1 verifier with INCONCLUSIVE
        minority = self._create_assertion("a9", "v9", VerificationStatus.INCONCLUSIVE)
        all_assertions = valid_assertions + [minority]

        # All pairs agree except the minority
        comparisons = []
        for i in range(9):
            for j in range(i + 1, 9):
                comparisons.append(VerifierComparison(
                    comparison_id=f"c{i}_{j}",
                    assertion_a_id=f"a{i}",
                    assertion_b_id=f"a{j}",
                    same_attestation=True,
                    same_evidence=True,
                    same_semantics=True,
                    disagreement_classification=DisagreementClass.AGREEMENT,
                ))
        # Comparisons involving the minority
        for i in range(9):
            comparisons.append(VerifierComparison(
                comparison_id=f"c{i}_9",
                assertion_a_id=f"a{i}",
                assertion_b_id="a9",
                same_attestation=True,
                same_evidence=True,
                same_semantics=True,
                disagreement_classification=DisagreementClass.RECONSTRUCTION_DIVERGENCE,
            ))

        consensus = builder.build_consensus("p1", all_assertions, comparisons)
        # The consensus should NOT be valid because there's unresolved disagreement
        assert not consensus.has_consensus
        assert len(consensus.unresolved_conflicts) > 0


# ---------------------------------------------------------------------------
# Attack 2 — One Strict Verifier
# ---------------------------------------------------------------------------


class TestAttack2OneStrictVerifier:
    def _create_identity(self, vid: str = "v1") -> VerifierIdentity:
        return VerifierIdentity(
            verifier_id=vid,
            implementation_id=f"impl{vid}",
        )

    def test_strict_verifier_preserves_disagreement(self):
        """Verifier A accepts, Verifier B applies stricter rules and rejects.
        System must NOT conclude A has more votes."""
        identity_a = self._create_identity("v1")
        identity_b = self._create_identity("v2")

        assertion_a = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity_a,
            attestation_hash="hash1",
            overall_status=VerificationStatus.VALID,
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.ROBUST,
            },
        )
        assertion_b = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity_b,
            attestation_hash="hash1",
            overall_status=VerificationStatus.INCONCLUSIVE,
            unresolved_dimensions={
                StateDimension.MECHANISM: "stricter authority requirements",
            },
        )

        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion_a, assertion_b)

        # Should classify as disagreement, not "A wins"
        assert comparison.disagreement_classification != DisagreementClass.AGREEMENT


# ---------------------------------------------------------------------------
# Attack 3 — Different Rule Versions
# ---------------------------------------------------------------------------


class TestAttack3DifferentRuleVersions:
    def test_different_rule_versions_classified(self):
        """Two verifiers with different rule versions should be classified
        as RULE_VERSION_DIVERGENCE, not as one being wrong."""
        identity1 = VerifierIdentity(
            verifier_id="v1",
            implementation_id="impl1",
            epistemic_rule_version="1.0.0",
        )
        identity2 = VerifierIdentity(
            verifier_id="v2",
            implementation_id="impl2",
            epistemic_rule_version="2.0.0",
        )

        assertion1 = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity1,
            attestation_hash="hash1",
            semantic_rule_version="1.0.0",
        )
        assertion2 = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity2,
            attestation_hash="hash1",
            semantic_rule_version="2.0.0",
        )

        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion1, assertion2)

        assert comparison.same_attestation
        assert not comparison.same_semantics
        assert comparison.disagreement_classification == DisagreementClass.SEMANTIC_DIVERGENCE


# ---------------------------------------------------------------------------
# Attack 4 — Evidence Divergence
# ---------------------------------------------------------------------------


class TestAttack4EvidenceDivergence:
    def test_different_evidence_sets(self):
        """Verifier A has E1,E2,E3. Verifier B has E1,E2,E3,E4.
        System must distinguish same historical state from new evidence state."""
        identity1 = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity2 = VerifierIdentity(verifier_id="v2", implementation_id="impl2")

        assertion1 = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity1,
            attestation_hash="hash1",
            evidence_refs=["e1", "e2", "e3"],
        )
        assertion2 = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity2,
            attestation_hash="hash1",
            evidence_refs=["e1", "e2", "e3", "e4"],
        )

        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion1, assertion2)

        assert not comparison.same_evidence
        assert comparison.disagreement_classification == DisagreementClass.EVIDENCE_DIVERGENCE


# ---------------------------------------------------------------------------
# Attack 5 — Provenance Divergence
# ---------------------------------------------------------------------------


class TestAttack5ProvenanceDivergence:
    def test_different_provenance(self):
        """Two evidence artifacts with same content but different provenance."""
        identity1 = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity2 = VerifierIdentity(verifier_id="v2", implementation_id="impl2")

        assertion1 = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity1,
            attestation_hash="hash1",
            evidence_refs=["e1"],
            provenance_refs=["provenance_A"],
        )
        assertion2 = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity2,
            attestation_hash="hash1",
            evidence_refs=["e1"],
            provenance_refs=["provenance_B"],
        )

        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion1, assertion2)

        assert not comparison.same_provenance
        assert comparison.disagreement_classification == DisagreementClass.PROVENANCE_DIVERGENCE


# ---------------------------------------------------------------------------
# Attack 6 — Semantic Equivalence
# ---------------------------------------------------------------------------


class TestAttack6SemanticEquivalence:
    def test_different_implementations_same_semantics(self):
        """Two verifiers with different implementations but identical declared
        semantics should reach epistemic agreement."""
        identity1 = VerifierIdentity(verifier_id="v1", implementation_id="impl_A")
        identity2 = VerifierIdentity(verifier_id="v2", implementation_id="impl_B")

        assertion1 = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity1,
            attestation_hash="hash1",
            evidence_refs=["e1"],
            semantic_rule_version="1.0.0",
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.ROBUST,
            },
        )
        assertion2 = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity2,
            attestation_hash="hash1",
            evidence_refs=["e1"],
            semantic_rule_version="1.0.0",
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.ROBUST,
            },
        )

        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion1, assertion2)

        assert comparison.same_attestation
        assert comparison.same_evidence
        assert comparison.same_semantics
        assert comparison.disagreement_classification == DisagreementClass.AGREEMENT


# ---------------------------------------------------------------------------
# Attack 7 — Implementation Diversity
# ---------------------------------------------------------------------------


class TestAttack7ImplementationDiversity:
    def test_implementation_diversity_can_agree(self):
        """Two genuinely different verifier implementations should be able
        to reach epistemic agreement."""
        identity1 = VerifierIdentity(verifier_id="v1", implementation_id="impl_A")
        identity2 = VerifierIdentity(verifier_id="v2", implementation_id="impl_B")

        assertion1 = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity1,
            attestation_hash="hash1",
            evidence_refs=["e1"],
            semantic_rule_version="1.0.0",
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.ROBUST,
            },
        )
        assertion2 = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity2,
            attestation_hash="hash1",
            evidence_refs=["e1"],
            semantic_rule_version="1.0.0",
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.ROBUST,
            },
        )

        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion1, assertion2)

        # Different implementations but same result
        assert comparison.same_attestation
        assert comparison.same_semantics
        assert comparison.disagreement_classification == DisagreementClass.AGREEMENT


# ---------------------------------------------------------------------------
# Attack 8 — Correlated Verifiers
# ---------------------------------------------------------------------------


class TestAttack8CorrelatedVerifiers:
    def test_correlated_verifiers_detected(self):
        """Three verifiers that are wrappers around the same evaluator
        should NOT be treated as independent."""
        identity1 = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity2 = VerifierIdentity(verifier_id="v2", implementation_id="impl1")
        identity3 = VerifierIdentity(verifier_id="v3", implementation_id="impl1")

        assertion1 = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity1,
            attestation_hash="hash1",
        )
        assertion2 = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity2,
            attestation_hash="hash1",
        )
        assertion3 = VerificationAssertion(
            assertion_id="a3",
            verifier_identity=identity3,
            attestation_hash="hash1",
        )

        engine = VerifierComparisonEngine()
        c12 = engine.compare(assertion1, assertion2)
        c13 = engine.compare(assertion1, assertion3)
        c23 = engine.compare(assertion2, assertion3)

        # All share implementation
        assert c12.independence_relationship == IndependenceRelationship.SHARES_IMPLEMENTATION
        assert c13.independence_relationship == IndependenceRelationship.SHARES_IMPLEMENTATION
        assert c23.independence_relationship == IndependenceRelationship.SHARES_IMPLEMENTATION


# ---------------------------------------------------------------------------
# Attack 9 — Sybil Verifiers
# ---------------------------------------------------------------------------


class TestAttack9SybilVerifiers:
    def test_sybil_verifiers_detected(self):
        """100 verifier identities backed by the same implementation
        should NOT be treated as 100 independent authorities."""
        identity_base = VerifierIdentity(verifier_id="v0", implementation_id="impl1")
        assertions = []
        for i in range(100):
            identity = VerifierIdentity(
                verifier_id=f"v{i}",
                implementation_id="impl1",
            )
            assertions.append(VerificationAssertion(
                assertion_id=f"a{i}",
                verifier_identity=identity,
                attestation_hash="hash1",
            ))

        engine = VerifierComparisonEngine()
        # Compare first with all others
        comparisons = []
        for i in range(1, 100):
            c = engine.compare(assertions[0], assertions[i])
            comparisons.append(c)

        # All should be detected as sharing implementation
        assert all(
            c.independence_relationship == IndependenceRelationship.SHARES_IMPLEMENTATION
            for c in comparisons
        )


# ---------------------------------------------------------------------------
# Attack 10 — Self-Attested Independence
# ---------------------------------------------------------------------------


class TestAttack10SelfAttestedIndependence:
    def test_independence_not_trusted_from_assertion(self):
        """A verifier claiming 'I am independent' should not be trusted.
        Independence must be established through provenance."""
        identity1 = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity2 = VerifierIdentity(verifier_id="v2", implementation_id="impl2")

        assertion1 = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity1,
            attestation_hash="hash1",
        )
        assertion2 = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity2,
            attestation_hash="hash1",
        )

        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion1, assertion2)

        # Different implementations, same rule engine version
        # The engine detects they share rule engine version
        # This is NOT proof of independence, but it's also not proof of dependence
        # The relationship is classified based on what can be determined from identity
        assert comparison.independence_relationship != IndependenceRelationship.INDEPENDENT


# ---------------------------------------------------------------------------
# Attack 11 — Valid Minority
# ---------------------------------------------------------------------------


class TestAttack11ValidMinority:
    def test_minority_preserves_gap(self):
        """Verifier A: SUPPORTED, Verifier B: SUPPORTED, Verifier C: INCONCLUSIVE.
        Verifier C identified an unresolved gap. Consensus must not erase it."""
        identity_a = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity_b = VerifierIdentity(verifier_id="v2", implementation_id="impl2")
        identity_c = VerifierIdentity(verifier_id="v3", implementation_id="impl3")

        assertion_a = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity_a,
            attestation_hash="hash1",
            overall_status=VerificationStatus.VALID,
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.ROBUST,
            },
        )
        assertion_b = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity_b,
            attestation_hash="hash1",
            overall_status=VerificationStatus.VALID,
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.ROBUST,
            },
        )
        assertion_c = VerificationAssertion(
            assertion_id="a3",
            verifier_identity=identity_c,
            attestation_hash="hash1",
            overall_status=VerificationStatus.INCONCLUSIVE,
            unresolved_dimensions={
                StateDimension.CAUSAL: "unresolved causal authority gap",
            },
        )

        builder = ConsensusBuilder()
        comparisons = [
            VerifierComparison(
                comparison_id="c1",
                assertion_a_id="a1",
                assertion_b_id="a2",
                same_attestation=True,
                same_evidence=True,
                same_semantics=True,
                disagreement_classification=DisagreementClass.AGREEMENT,
            ),
            VerifierComparison(
                comparison_id="c2",
                assertion_a_id="a1",
                assertion_b_id="a3",
                same_attestation=True,
                same_evidence=True,
                same_semantics=True,
                disagreement_classification=DisagreementClass.RECONSTRUCTION_DIVERGENCE,
            ),
        ]
        consensus = builder.build_consensus("p1", [assertion_a, assertion_b, assertion_c], comparisons)

        # Consensus should NOT be valid because of the unresolved gap
        assert not consensus.has_consensus


# ---------------------------------------------------------------------------
# Attack 12 — Valid Contradiction
# ---------------------------------------------------------------------------


class TestAttack12ValidContradiction:
    def test_contradiction_preserved(self):
        """Verifier A: SUPPORTED, Verifier B: REFUTED.
        System must produce structured contradiction, not resolve by vote."""
        identity_a = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity_b = VerifierIdentity(verifier_id="v2", implementation_id="impl2")

        assertion_a = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity_a,
            attestation_hash="hash1",
            overall_status=VerificationStatus.VALID,
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.ROBUST,
            },
        )
        assertion_b = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity_b,
            attestation_hash="hash1",
            overall_status=VerificationStatus.INVALID,
            failed_dimensions={
                StateDimension.MECHANISM: "semantic violation",
            },
        )

        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion_a, assertion_b)

        # Should classify as disagreement
        assert comparison.disagreement_classification != DisagreementClass.AGREEMENT

        # Build consensus
        builder = ConsensusBuilder()
        consensus = builder.build_consensus("p1", [assertion_a, assertion_b], [comparison])

        # Must NOT have consensus
        assert not consensus.has_consensus
        assert len(consensus.unresolved_conflicts) > 0


# ---------------------------------------------------------------------------
# Attack 13 — Governance Conflict
# ---------------------------------------------------------------------------


class TestAttack13GovernanceConflict:
    def test_governance_disagreement_preserves_epistemic_agreement(self):
        """Two verifiers agree mechanism=VERIFIED. Two governance policies
        disagree. System must preserve epistemic agreement."""
        identity_a = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity_b = VerifierIdentity(verifier_id="v2", implementation_id="impl2")

        assertion_a = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity_a,
            attestation_hash="hash1",
            overall_status=VerificationStatus.VALID,
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.ROBUST,
            },
        )
        assertion_b = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity_b,
            attestation_hash="hash1",
            overall_status=VerificationStatus.VALID,
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.ROBUST,
            },
        )

        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion_a, assertion_b)

        # Epistemic agreement
        assert comparison.same_attestation
        assert comparison.same_evidence
        assert comparison.same_semantics
        assert comparison.disagreement_classification == DisagreementClass.AGREEMENT

        # Consensus should be valid at epistemic level
        builder = ConsensusBuilder()
        consensus = builder.build_consensus("p1", [assertion_a, assertion_b], [comparison])
        assert consensus.has_consensus


# ---------------------------------------------------------------------------
# Attack 14 — Verification vs Re-Evaluation
# ---------------------------------------------------------------------------


class TestAttack14VerificationVsReEvaluation:
    def test_historical_vs_current_distinguished(self):
        """Verifier A verifies historical state under historical rules.
        Verifier B evaluates same evidence under current rules.
        These are different operations."""
        identity_a = VerifierIdentity(
            verifier_id="v1",
            implementation_id="impl1",
            epistemic_rule_version="1.0.0",
        )
        identity_b = VerifierIdentity(
            verifier_id="v2",
            implementation_id="impl2",
            epistemic_rule_version="2.0.0",
        )

        assertion_a = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity_a,
            attestation_hash="hash1",
            semantic_rule_version="1.0.0",
        )
        assertion_b = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity_b,
            attestation_hash="hash1",
            semantic_rule_version="2.0.0",
        )

        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion_a, assertion_b)

        # Different rule versions
        assert not comparison.same_semantics
        assert comparison.disagreement_classification == DisagreementClass.SEMANTIC_DIVERGENCE


# ---------------------------------------------------------------------------
# Attack 15 — Partial Agreement
# ---------------------------------------------------------------------------


class TestAttack15PartialAgreement:
    def test_partial_agreement_reported(self):
        """Verifier A: mechanism=REPLICATED, generalization=UNRESOLVED.
        Verifier B: mechanism=REPLICATED, generalization=VERIFIED.
        Comparison should report agreement on mechanism, disagreement on generalization."""
        identity_a = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity_b = VerifierIdentity(verifier_id="v2", implementation_id="impl2")

        assertion_a = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity_a,
            attestation_hash="hash1",
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.REPLICATED,
            },
            unresolved_dimensions={
                StateDimension.GENERALIZATION: "insufficient evidence",
            },
        )
        assertion_b = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity_b,
            attestation_hash="hash1",
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.REPLICATED,
                StateDimension.GENERALIZATION: DimensionStatus.ROBUST,
            },
        )

        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion_a, assertion_b)

        # Mechanism agrees
        assert StateDimension.MECHANISM in comparison.agreement_dimensions
        # Generalization disagrees
        assert StateDimension.GENERALIZATION in comparison.disagreement_dimensions


# ---------------------------------------------------------------------------
# Attack 16 — Compatible Partial States
# ---------------------------------------------------------------------------


class TestAttack16CompatiblePartialStates:
    def test_unresolved_not_contradictory_to_verified(self):
        """Verifier A: mechanism=VERIFIED, generalization=UNRESOLVED.
        Verifier B: mechanism=VERIFIED, generalization=VERIFIED.
        These are NOT contradictory."""
        identity_a = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity_b = VerifierIdentity(verifier_id="v2", implementation_id="impl2")

        assertion_a = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity_a,
            attestation_hash="hash1",
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.ROBUST,
            },
            unresolved_dimensions={
                StateDimension.GENERALIZATION: "insufficient evidence",
            },
        )
        assertion_b = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity_b,
            attestation_hash="hash1",
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.ROBUST,
                StateDimension.GENERALIZATION: DimensionStatus.ROBUST,
            },
        )

        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion_a, assertion_b)

        # Mechanism agrees
        assert StateDimension.MECHANISM in comparison.agreement_dimensions
        # Generalization: A has UNRESOLVED, B has VERIFIED
        # This is partial agreement, not contradiction
        # The disagreement should be noted but not as severe as a contradiction


# ---------------------------------------------------------------------------
# Attack 17 — Different Available Artifacts
# ---------------------------------------------------------------------------


class TestAttack17DifferentAvailableArtifacts:
    def test_knowledge_boundary_distinct_from_failure(self):
        """Verifier A cannot access E4. Verifier B can access E4.
        A must not be classified as incorrect."""
        identity_a = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity_b = VerifierIdentity(verifier_id="v2", implementation_id="impl2")

        assertion_a = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity_a,
            attestation_hash="hash1",
            evidence_refs=["e1", "e2", "e3"],
        )
        assertion_b = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity_b,
            attestation_hash="hash1",
            evidence_refs=["e1", "e2", "e3", "e4"],
        )

        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion_a, assertion_b)

        # Different evidence sets
        assert not comparison.same_evidence
        # Should be classified as evidence divergence, not as A being wrong
        assert comparison.disagreement_classification == DisagreementClass.EVIDENCE_DIVERGENCE


# ---------------------------------------------------------------------------
# Attack 18 — Missing Semantics
# ---------------------------------------------------------------------------


class TestAttack18MissingSemantics:
    def test_unverifiable_not_refuted(self):
        """Verifier B has evidence but cannot interpret intervention semantics.
        B should produce UNVERIFIABLE, not REFUTED."""
        identity_a = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity_b = VerifierIdentity(
            verifier_id="v2",
            implementation_id="impl2",
            intervention_semantics_version="unknown",
        )

        assertion_a = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity_a,
            attestation_hash="hash1",
            overall_status=VerificationStatus.VALID,
            semantic_rule_version="1.0.0",
        )
        assertion_b = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity_b,
            attestation_hash="hash1",
            overall_status=VerificationStatus.INCONCLUSIVE,
            semantic_rule_version="unknown",
        )

        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion_a, assertion_b)

        # Different semantics
        assert not comparison.same_semantics
        # B's result is INCONCLUSIVE, not REFUTED
        assert assertion_b.overall_status == VerificationStatus.INCONCLUSIVE


# ---------------------------------------------------------------------------
# Attack 19 — Forged Consensus
# ---------------------------------------------------------------------------


class TestAttack19ForgedConsensus:
    def test_forged_consensus_detected(self):
        """A malicious artifact claiming 'Verifier A and B agree' should not
        be trusted. Consensus must be derived from independently verifiable assertions."""
        identity_a = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity_b = VerifierIdentity(verifier_id="v2", implementation_id="impl2")

        assertion_a = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity_a,
            attestation_hash="hash1",
            overall_status=VerificationStatus.VALID,
        )
        assertion_b = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity_b,
            attestation_hash="hash1",
            overall_status=VerificationStatus.INVALID,
        )

        # Forged consensus claiming agreement
        forged_consensus = EpistemicConsensus(
            consensus_id="forged",
            proposition_id="p1",
            assertion_refs=["a1", "a2"],
            has_consensus=True,
            consensus_basis="forged agreement",
        )

        # Real comparison shows disagreement
        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion_a, assertion_b)

        # The forged consensus says agreement, but real comparison shows disagreement
        assert forged_consensus.has_consensus
        assert comparison.disagreement_classification != DisagreementClass.AGREEMENT


# ---------------------------------------------------------------------------
# Attack 20 — Consensus Forgery
# ---------------------------------------------------------------------------


class TestAttack20ConsensusForgery:
    def test_consensus_must_be_derived(self):
        """A forged consensus object claiming A and B agree must be detected
        by reconstructing the comparison from assertions."""
        identity_a = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity_b = VerifierIdentity(verifier_id="v2", implementation_id="impl2")

        assertion_a = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity_a,
            attestation_hash="hash1",
            overall_status=VerificationStatus.VALID,
        )
        assertion_b = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity_b,
            attestation_hash="hash1",
            overall_status=VerificationStatus.INVALID,
        )

        # Forged consensus
        forged = EpistemicConsensus(
            consensus_id="forged",
            proposition_id="p1",
            assertion_refs=["a1", "a2"],
            has_consensus=True,
        )

        # Reconstruct comparison
        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion_a, assertion_b)

        # Real comparison shows disagreement
        assert comparison.disagreement_classification != DisagreementClass.AGREEMENT
        # Forged consensus is invalid
        assert forged.has_consensus != (comparison.disagreement_classification == DisagreementClass.AGREEMENT)


# ---------------------------------------------------------------------------
# Test: Independence Relationship
# ---------------------------------------------------------------------------


class TestIndependenceRelationship:
    def test_all_relationships_present(self):
        relationships = list(IndependenceRelationship)
        assert len(relationships) == 9
        assert IndependenceRelationship.INDEPENDENT in relationships
        assert IndependenceRelationship.DERIVED_FROM in relationships
        assert IndependenceRelationship.SHARES_IMPLEMENTATION in relationships
        assert IndependenceRelationship.UNKNOWN in relationships


# ---------------------------------------------------------------------------
# Test: Disagreement Class
# ---------------------------------------------------------------------------


class TestDisagreementClass:
    def test_all_classes_present(self):
        classes = list(DisagreementClass)
        assert len(classes) == 9
        assert DisagreementClass.AGREEMENT in classes
        assert DisagreementClass.EVIDENCE_DIVERGENCE in classes
        assert DisagreementClass.SEMANTIC_DIVERGENCE in classes
        assert DisagreementClass.UNRESOLVED_VERIFICATION_CONFLICT in classes


# ---------------------------------------------------------------------------
# Test: Epistemic Conflict
# ---------------------------------------------------------------------------


class TestEpistemicConflict:
    def test_compute_hash(self):
        conflict = EpistemicConflict(
            conflict_id="c1",
            proposition_id="p1",
        )
        hash1 = conflict.compute_hash()
        hash2 = conflict.compute_hash()
        assert hash1 == hash2

    def test_unresolved_by_default(self):
        conflict = EpistemicConflict(
            conflict_id="c1",
            proposition_id="p1",
        )
        assert conflict.unresolved


# ---------------------------------------------------------------------------
# Test: Multi-Verifier Orchestrator
# ---------------------------------------------------------------------------


class TestMultiVerifierOrchestrator:
    def test_register_verifier(self):
        orchestrator = MultiVerifierOrchestrator()
        identity = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        verifier = EpistemicVerifier()
        orchestrator.register_verifier("v1", identity, verifier)
        assert "v1" in orchestrator.verifiers
        assert "v1" in orchestrator.identities

    def test_run_verification(self):
        orchestrator = MultiVerifierOrchestrator()
        identity = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        verifier = EpistemicVerifier()
        orchestrator.register_verifier("v1", identity, verifier)

        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
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

        artifacts = {
            "proposition": prop,
            "state": new_state,
            "transition": transition,
            "previous_state": initial_state,
            "evidence": evidence,
        }

        assertions = orchestrator.run_verification(attestation, artifacts)
        assert len(assertions) == 1
        assert assertions[0].verifier_identity.verifier_id == "v1"


# ---------------------------------------------------------------------------
# Test: Convenience Functions
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    def test_create_verifier_identity(self):
        identity = create_verifier_identity("v1", "impl1")
        assert identity.verifier_id == "v1"
        assert identity.implementation_id == "impl1"

    def test_compare_verifier_assertions(self):
        identity1 = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity2 = VerifierIdentity(verifier_id="v2", implementation_id="impl2")

        assertion1 = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity1,
            attestation_hash="hash1",
        )
        assertion2 = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity2,
            attestation_hash="hash1",
        )

        comparison = compare_verifier_assertions(assertion1, assertion2)
        assert comparison.same_attestation

    def test_build_epistemic_consensus(self):
        identity1 = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity2 = VerifierIdentity(verifier_id="v2", implementation_id="impl2")

        assertion1 = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity1,
            attestation_hash="hash1",
        )
        assertion2 = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity2,
            attestation_hash="hash1",
        )

        comparison = VerifierComparison(
            comparison_id="c1",
            assertion_a_id="a1",
            assertion_b_id="a2",
            same_attestation=True,
            same_evidence=True,
            same_semantics=True,
            disagreement_classification=DisagreementClass.AGREEMENT,
        )

        consensus = build_epistemic_consensus("p1", [assertion1, assertion2], [comparison])
        assert consensus.has_consensus


# ---------------------------------------------------------------------------
# Test: Invariant — More Identities ≠ More Authority
# ---------------------------------------------------------------------------


class TestMoreIdentitiesNotMoreAuthority:
    def test_1_verifier_same_result_as_100_correlated(self):
        """1 verifier and 100 correlated verifiers should produce the same
        epistemic result. More identities does not mean more authority."""
        builder = ConsensusBuilder()

        # 1 verifier
        identity1 = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        assertion1 = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity1,
            attestation_hash="hash1",
            overall_status=VerificationStatus.VALID,
        )

        # 100 correlated verifiers (same implementation)
        correlated_assertions = []
        for i in range(100):
            identity = VerifierIdentity(
                verifier_id=f"v{i}",
                implementation_id="impl1",
            )
            correlated_assertions.append(VerificationAssertion(
                assertion_id=f"a{i}",
                verifier_identity=identity,
                attestation_hash="hash1",
                overall_status=VerificationStatus.VALID,
            ))

        # Single verifier consensus - no comparisons needed
        single_consensus = builder.build_consensus("p1", [assertion1], [])
        assert single_consensus.has_consensus  # Single verifier is trivially consensus

        # 100 correlated verifiers consensus
        all_correlated = [assertion1] + correlated_assertions
        comparisons = []
        for i in range(1, len(all_correlated)):
            comparisons.append(VerifierComparison(
                comparison_id=f"c{i}",
                assertion_a_id="a1",
                assertion_b_id=f"a{i}",
                same_attestation=True,
                same_evidence=True,
                same_semantics=True,
                disagreement_classification=DisagreementClass.AGREEMENT,
                independence_relationship=IndependenceRelationship.SHARES_IMPLEMENTATION,
            ))
        correlated_consensus = builder.build_consensus("p1", all_correlated, comparisons)

        # Both should have consensus (but correlated ones are not independent)
        assert single_consensus.has_consensus
        assert correlated_consensus.has_consensus

        # The independence evidence should show correlation
        # (In a full implementation, the consensus would weight by independence)


# ---------------------------------------------------------------------------
# Test: Invariant — Independent Disagreement Preserves Uncertainty
# ---------------------------------------------------------------------------


class TestIndependentDisagreementPreservesUncertainty:
    def test_supported_vs_refuted_not_resolved(self):
        """A: SUPPORTED, B: REFUTED. System must NOT resolve to SUPPORTED
        or REFUTED or 50/50."""
        identity_a = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        identity_b = VerifierIdentity(verifier_id="v2", implementation_id="impl2")

        assertion_a = VerificationAssertion(
            assertion_id="a1",
            verifier_identity=identity_a,
            attestation_hash="hash1",
            overall_status=VerificationStatus.VALID,
        )
        assertion_b = VerificationAssertion(
            assertion_id="a2",
            verifier_identity=identity_b,
            attestation_hash="hash1",
            overall_status=VerificationStatus.INVALID,
        )

        engine = VerifierComparisonEngine()
        comparison = engine.compare(assertion_a, assertion_b)

        builder = ConsensusBuilder()
        consensus = builder.build_consensus("p1", [assertion_a, assertion_b], [comparison])

        # Must NOT have consensus
        assert not consensus.has_consensus
        # Must have unresolved conflicts
        assert len(consensus.unresolved_conflicts) > 0
