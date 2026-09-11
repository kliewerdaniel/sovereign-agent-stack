"""Authority Boundary Adjudication Engine.

This module implements the adjudication of authority boundaries.
It takes a boundary, runtime evidence, static evidence, and declarations,
and produces a BoundaryAdjudication with classification and governance disposition.

Central principle:
    DISCOVERY OF AN AUTHORITY ESCAPE IS AN EPISTEMIC RESULT.
    WHETHER THAT ESCAPE IS ACCEPTABLE IS A GOVERNANCE DECISION.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from research.examples.self_audit.authority_boundary import (
    AuthorityBasis,
    AuthorityBoundary,
    AuthorityOwner,
    BoundaryAdjudication,
    BoundaryClassification,
    ConsequenceType,
    DelegationDeclaration,
    GovernanceDisposition,
    GovernanceRecommendation,
    GovernanceSeparation,
    InvariantChecker,
    TrustDeclaration,
)


@dataclass
class AdjudicationContext:
    """Context for boundary adjudication."""

    boundary: AuthorityBoundary
    runtime_events: list[dict[str, Any]] = field(default_factory=list)
    static_hypotheses: list[dict[str, Any]] = field(default_factory=list)
    reconciliation_results: list[dict[str, Any]] = field(default_factory=list)
    authority_reconstructions: list[dict[str, Any]] = field(default_factory=list)
    declarations: list[dict[str, Any]] = field(default_factory=list)
    governance_policies: list[dict[str, Any]] = field(default_factory=list)
    temporal_context: str = "current"
    environment: str = "local"
    scope: str = "controlled"


class AuthorityBoundaryAdjudicator:
    """Adjudicates authority boundaries."""

    def __init__(self):
        self.invariant_checker = InvariantChecker()
        self.governance_separation = GovernanceSeparation()

    def adjudicate(self, context: AdjudicationContext) -> BoundaryAdjudication:
        """Adjudicate an authority boundary."""
        boundary = context.boundary

        # Step 1: Determine authority basis
        authority_basis = self._determine_authority_basis(context)

        # Step 2: Classify the boundary
        classification = self._classify_boundary(context, authority_basis)

        # Step 3: Determine governance disposition
        governance_disposition = self._determine_governance_disposition(
            context, classification, authority_basis
        )

        # Step 4: Compute confidence
        confidence = self._compute_confidence(context, classification, authority_basis)

        # Step 5: Generate findings
        findings = self._generate_findings(context, classification, authority_basis)

        # Step 6: Generate recommendations
        recommendations = self._generate_recommendations(
            context, classification, governance_disposition
        )

        # Step 7: Identify unresolved questions
        unresolved = self._identify_unresolved_questions(context, classification)

        # Step 8: Identify limitations
        limitations = self._identify_limitations(context)

        # Step 9: Build provenance chain
        provenance_chain = self._build_provenance_chain(context)

        # Step 10: Build adjudication
        adjudication = BoundaryAdjudication(
            adjudication_id=f"adj_{uuid.uuid4().hex[:12]}",
            boundary=boundary,
            classification=classification,
            authority_basis=authority_basis,
            governance_disposition=governance_disposition,
            confidence=confidence,
            runtime_evidence=context.runtime_events,
            static_evidence=context.static_hypotheses,
            reconciliation_evidence=context.reconciliation_results,
            authority_reconstruction=context.authority_reconstructions[0] if context.authority_reconstructions else None,
            declarations=context.declarations,
            findings=findings,
            recommendations=recommendations,
            unresolved_questions=unresolved,
            limitations=limitations,
            provenance_chain=provenance_chain,
        )

        return adjudication

    def _determine_authority_basis(self, context: AdjudicationContext) -> AuthorityBasis:
        """Determine the authority basis for a boundary."""
        boundary = context.boundary

        # Check for explicit declarations
        for declaration in context.declarations:
            decl_type = declaration.get("declaration_type", "")
            if decl_type == "delegation_declaration":
                # Check if delegation is active
                if declaration.get("is_active", False):
                    return AuthorityBasis.EXPLICIT_DELEGATION
            elif decl_type == "trust_declaration":
                if declaration.get("is_active", False):
                    return AuthorityBasis.TRUST_DECLARATION
            elif decl_type == "policy_declaration":
                return AuthorityBasis.GOVERNANCE_POLICY

        # Check for protocol authority
        if boundary.declared_mechanism == "protocol":
            return AuthorityBasis.PROTOCOL_DERIVATION

        # Check for ambient privilege
        if boundary.declared_mechanism == "ambient":
            return AuthorityBasis.AMBIENT_PRIVILEGE

        # Check for historical practice
        if context.runtime_events and not context.declarations:
            return AuthorityBasis.HISTORICAL_PRACTICE

        return AuthorityBasis.UNKNOWN

    def _classify_boundary(
        self,
        context: AdjudicationContext,
        authority_basis: AuthorityBasis,
    ) -> BoundaryClassification:
        """Classify the boundary."""
        boundary = context.boundary

        # Check for explicit prohibition
        for policy in context.governance_policies:
            if policy.get("prohibits", False):
                if boundary.actor in policy.get("actors", []):
                    return BoundaryClassification.UNAUTHORIZED_ESCAPE

        # Classify based on authority basis
        if authority_basis == AuthorityBasis.PROTOCOL_DERIVATION:
            return BoundaryClassification.INTENTIONAL_PROTOCOL_AUTHORITY

        elif authority_basis == AuthorityBasis.EXPLICIT_DELEGATION:
            # Check delegation scope
            for declaration in context.declarations:
                if declaration.get("declaration_type") == "delegation_declaration":
                    scope = declaration.get("scope", {})
                    if self._is_within_scope(boundary, scope):
                        return BoundaryClassification.EXPLICIT_DELEGATION
                    else:
                        return BoundaryClassification.AUTHORITY_MISMATCH

        elif authority_basis == AuthorityBasis.TRUST_DECLARATION:
            return BoundaryClassification.TRUSTED_SUBSYSTEM

        elif authority_basis == AuthorityBasis.HISTORICAL_PRACTICE:
            return BoundaryClassification.LEGACY_UNGOVERNED

        elif authority_basis == AuthorityBasis.AMBIENT_PRIVILEGE:
            return BoundaryClassification.RECONSTRUCTION_FAILURE

        elif authority_basis == AuthorityBasis.GOVERNANCE_POLICY:
            return BoundaryClassification.INTENTIONAL_PROTOCOL_AUTHORITY

        return BoundaryClassification.INCONCLUSIVE

    def _determine_governance_disposition(
        self,
        context: AdjudicationContext,
        classification: BoundaryClassification,
        authority_basis: AuthorityBasis,
    ) -> GovernanceDisposition:
        """Determine the governance disposition."""
        # Check for explicit prohibition
        for policy in context.governance_policies:
            if policy.get("prohibits", False):
                return GovernanceDisposition.PROHIBITED

        # Check for explicit acceptance
        for policy in context.governance_policies:
            if policy.get("accepts", False):
                return GovernanceDisposition.ACCEPTED

        # Classify based on boundary classification
        if classification == BoundaryClassification.INTENTIONAL_PROTOCOL_AUTHORITY:
            return GovernanceDisposition.ACCEPTED

        elif classification == BoundaryClassification.EXPLICIT_DELEGATION:
            return GovernanceDisposition.DELEGATED

        elif classification == BoundaryClassification.TRUSTED_SUBSYSTEM:
            return GovernanceDisposition.CONSTRAINED

        elif classification == BoundaryClassification.LEGACY_UNGOVERNED:
            return GovernanceDisposition.PENDING_REVIEW

        elif classification == BoundaryClassification.UNAUTHORIZED_ESCAPE:
            return GovernanceDisposition.REJECTED

        elif classification == BoundaryClassification.AUTHORITY_MISMATCH:
            return GovernanceDisposition.PENDING_REVIEW

        elif classification == BoundaryClassification.RECONSTRUCTION_FAILURE:
            return GovernanceDisposition.PENDING_REVIEW

        return GovernanceDisposition.INCONCLUSIVE

    def _compute_confidence(
        self,
        context: AdjudicationContext,
        classification: BoundaryClassification,
        authority_basis: AuthorityBasis,
    ) -> float:
        """Compute confidence in the adjudication."""
        confidence = 0.5  # Base confidence

        # Increase confidence with more evidence
        if context.runtime_events:
            confidence += 0.1
        if context.static_hypotheses:
            confidence += 0.1
        if context.reconciliation_results:
            confidence += 0.1
        if context.declarations:
            confidence += 0.1
        if context.authority_reconstructions:
            confidence += 0.05
        if context.governance_policies:
            confidence += 0.05

        # Decrease confidence for inconclusive classifications
        if classification == BoundaryClassification.INCONCLUSIVE:
            confidence *= 0.7

        # Decrease confidence for unknown authority basis
        if authority_basis == AuthorityBasis.UNKNOWN:
            confidence *= 0.8

        return min(confidence, 1.0)

    def _generate_findings(
        self,
        context: AdjudicationContext,
        classification: BoundaryClassification,
        authority_basis: AuthorityBasis,
    ) -> list[str]:
        """Generate findings."""
        findings = []

        if classification == BoundaryClassification.INTENTIONAL_PROTOCOL_AUTHORITY:
            findings.append("Boundary has intentional protocol authority")
            findings.append("Authority is derived through the canonical chain")

        elif classification == BoundaryClassification.EXPLICIT_DELEGATION:
            findings.append("Boundary has explicit delegation of authority")
            findings.append("Authority is bounded by delegation scope")

        elif classification == BoundaryClassification.TRUSTED_SUBSYSTEM:
            findings.append("Boundary is a trusted subsystem")
            findings.append("Subsystem operates outside the canonical protocol")
            findings.append("Trust declaration provides authority basis")

        elif classification == BoundaryClassification.LEGACY_UNGOVERNED:
            findings.append("Boundary has historical practice but no authority declaration")
            findings.append("Legacy operation requires governance review")

        elif classification == BoundaryClassification.UNAUTHORIZED_ESCAPE:
            findings.append("Boundary is an unauthorized authority escape")
            findings.append("No authority basis found for this boundary")

        elif classification == BoundaryClassification.AUTHORITY_MISMATCH:
            findings.append("Boundary has authority mismatch")
            findings.append("Delegation scope does not cover this boundary")

        elif classification == BoundaryClassification.RECONSTRUCTION_FAILURE:
            findings.append("Boundary authority cannot be reconstructed")
            findings.append("Ambient privilege detected without protocol participation")

        elif classification == BoundaryClassification.INCONCLUSIVE:
            findings.append("Boundary classification is inconclusive")
            findings.append("Insufficient evidence to determine authority status")

        # Add runtime evidence findings
        if context.runtime_events:
            findings.append(f"Runtime evidence: {len(context.runtime_events)} events observed")

        # Add declaration findings
        if context.declarations:
            findings.append(f"Declarations: {len(context.declarations)} found")
        else:
            findings.append("No authority declarations found")

        return findings

    def _generate_recommendations(
        self,
        context: AdjudicationContext,
        classification: BoundaryClassification,
        governance_disposition: GovernanceDisposition,
    ) -> list[str]:
        """Generate governance recommendations."""
        recommendations = []

        if classification == BoundaryClassification.INTENTIONAL_PROTOCOL_AUTHORITY:
            recommendations.append("No action required - boundary is properly governed")

        elif classification == BoundaryClassification.EXPLICIT_DELEGATION:
            recommendations.append("Verify delegation scope covers intended operations")
            recommendations.append("Document delegation provenance")

        elif classification == BoundaryClassification.TRUSTED_SUBSYSTEM:
            recommendations.append("Document trust basis and scope")
            recommendations.append("Consider migrating to protocol authority")
            recommendations.append("Add provenance requirements for trust declarations")

        elif classification == BoundaryClassification.LEGACY_UNGOVERNED:
            recommendations.append("Review legacy operation for governance compliance")
            recommendations.append("Create authority declaration or migrate to protocol")
            recommendations.append("Document historical context and intent")

        elif classification == BoundaryClassification.UNAUTHORIZED_ESCAPE:
            recommendations.append("Review boundary for governance compliance")
            recommendations.append("Determine if boundary should be authorized or prohibited")
            recommendations.append("Document findings for governance review")

        elif classification == BoundaryClassification.AUTHORITY_MISMATCH:
            recommendations.append("Review delegation scope")
            recommendations.append("Update delegation or constrain boundary")

        elif classification == BoundaryClassification.RECONSTRUCTION_FAILURE:
            recommendations.append("Investigate ambient privilege usage")
            recommendations.append("Migrate to protocol authority if appropriate")

        elif classification == BoundaryClassification.INCONCLUSIVE:
            recommendations.append("Gather more evidence")
            recommendations.append("Review declarations and policies")

        return recommendations

    def _identify_unresolved_questions(
        self,
        context: AdjudicationContext,
        classification: BoundaryClassification,
    ) -> list[str]:
        """Identify unresolved questions."""
        unresolved = []

        if classification == BoundaryClassification.INCONCLUSIVE:
            unresolved.append("What is the intended authority basis for this boundary?")
            unresolved.append("Is there a trust declaration or delegation that applies?")

        if not context.declarations:
            unresolved.append("Are there any authority declarations that apply to this boundary?")

        if not context.governance_policies:
            unresolved.append("What governance policies apply to this boundary?")

        if classification == BoundaryClassification.LEGACY_UNGOVERNED:
            unresolved.append("What is the historical context for this boundary?")
            unresolved.append("Is this boundary intentionally ungoverned?")

        if classification == BoundaryClassification.TRUSTED_SUBSYSTEM:
            unresolved.append("What is the trust basis for this subsystem?")
            unresolved.append("What are the constraints on this trust?")

        return unresolved

    def _identify_limitations(self, context: AdjudicationContext) -> list[str]:
        """Identify limitations of the adjudication."""
        limitations = []

        if len(context.runtime_events) < 5:
            limitations.append("Limited runtime evidence")

        if not context.declarations:
            limitations.append("No authority declarations provided")

        if not context.governance_policies:
            limitations.append("No governance policies provided")

        if not context.authority_reconstructions:
            limitations.append("No authority reconstruction available")

        limitations.append("Adjudication is based on provided evidence only")
        limitations.append("Governance disposition is a recommendation, not an enforcement directive")

        return limitations

    def _build_provenance_chain(self, context: AdjudicationContext) -> list[str]:
        """Build the provenance chain for the adjudication."""
        chain = []

        # Add runtime evidence IDs
        for event in context.runtime_events:
            if "event_id" in event:
                chain.append(f"runtime:{event['event_id']}")

        # Add static hypothesis IDs
        for hypothesis in context.static_hypotheses:
            if "hypothesis_id" in hypothesis:
                chain.append(f"static:{hypothesis['hypothesis_id']}")

        # Add reconciliation IDs
        for result in context.reconciliation_results:
            if "reconciliation_id" in result:
                chain.append(f"reconciliation:{result['reconciliation_id']}")

        # Add declaration IDs
        for declaration in context.declarations:
            if "declaration_id" in declaration:
                chain.append(f"declaration:{declaration['declaration_id']}")

        # Add policy IDs
        for policy in context.governance_policies:
            if "policy_id" in policy:
                chain.append(f"policy:{policy['policy_id']}")

        return chain

    def _is_within_scope(
        self,
        boundary: AuthorityBoundary,
        scope: dict[str, Any],
    ) -> bool:
        """Check if a boundary is within a delegation scope."""
        # Check actor
        if "actors" in scope and boundary.actor not in scope["actors"]:
            return False

        # Check operation
        if "operations" in scope and boundary.operation not in scope["operations"]:
            return False

        # Check resource
        if "resources" in scope and boundary.resource not in scope["resources"]:
            return False

        # Check consequence type
        if "consequence_types" in scope:
            if boundary.consequence_type.value not in scope["consequence_types"]:
                return False

        return True


# ---------------------------------------------------------------------------
# Argopack Scenarios
# ---------------------------------------------------------------------------


class ArgopackScenarioBuilder:
    """Builds adjudication scenarios for the Argopack subprocess path."""

    @staticmethod
    def build_boundary() -> AuthorityBoundary:
        """Build the Argopack authority boundary."""
        return AuthorityBoundary(
            boundary_id="argopack_subprocess",
            source_domain="sas.argopack",
            destination_domain="os.process",
            actor="argopack",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="python -m sas",
            operation="subprocess.run",
            temporal_scope="unbounded",
            provenance_requirements=["declaration_id", "governance_policy"],
            reconstruction_requirements=["authority_chain", "provenance_record"],
            constraints=["timeout=30", "capture_output=True"],
        )

    @staticmethod
    def build_runtime_evidence() -> list[dict[str, Any]]:
        """Build runtime evidence for Argopack."""
        return [
            {
                "event_id": "evt_001",
                "event_type": "subprocess_create",
                "actor": "argopack",
                "component": "argopack.py",
                "operation": "subprocess.run",
                "resource": "python -m sas --help",
                "consequence_type": "external_consequential",
                "result": "exit_code=0",
                "capability_id": None,
                "authorization_id": None,
                "provenance_id": None,
            }
        ]

    @staticmethod
    def build_static_evidence() -> list[dict[str, Any]]:
        """Build static evidence for Argopack."""
        return [
            {
                "hypothesis_id": "hyp_0001",
                "source": "src/sas/argopack.py",
                "target": "subprocess.run",
                "operation": "subprocess_execution",
                "consequence_type": "external_consequential",
                "static_evidence": "subprocess.run(cmd, capture_output=True, text=True, timeout=30)",
                "expected_authority_boundary": "none",
                "predicted_classification": "authority_escape",
                "confidence": 0.6,
            }
        ]

    @staticmethod
    def build_reconciliation_evidence() -> list[dict[str, Any]]:
        """Build reconciliation evidence for Argopack."""
        return [
            {
                "reconciliation_id": "rec_hyp_0001",
                "classification": "authority_escape",
                "confidence": 0.75,
                "epistemic_state": "unauthorized",
                "runtime_events_matched": 1,
            }
        ]

    @staticmethod
    def build_authority_reconstruction() -> list[dict[str, Any]]:
        """Build authority reconstruction for Argopack."""
        return [
            {
                "state": "unauthorized",
                "capability_present": False,
                "authorization_present": False,
                "provenance_present": False,
                "missing_links": [
                    "sovereign_root", "policy", "governance",
                    "authorization", "capability", "receipt", "provenance"
                ],
            }
        ]

    @staticmethod
    def build_scenario_a_no_declaration() -> AdjudicationContext:
        """Scenario A: No declaration."""
        return AdjudicationContext(
            boundary=ArgopackScenarioBuilder.build_boundary(),
            runtime_events=ArgopackScenarioBuilder.build_runtime_evidence(),
            static_hypotheses=ArgopackScenarioBuilder.build_static_evidence(),
            reconciliation_results=ArgopackScenarioBuilder.build_reconciliation_evidence(),
            authority_reconstructions=ArgopackScenarioBuilder.build_authority_reconstruction(),
            declarations=[],
            governance_policies=[],
        )

    @staticmethod
    def build_scenario_b_trust_declaration() -> AdjudicationContext:
        """Scenario B: Explicit trust declaration."""
        boundary = ArgopackScenarioBuilder.build_boundary()
        boundary = AuthorityBoundary(
            boundary_id=boundary.boundary_id,
            source_domain=boundary.source_domain,
            destination_domain=boundary.destination_domain,
            actor=boundary.actor,
            consequence_type=boundary.consequence_type,
            resource=boundary.resource,
            operation=boundary.operation,
            temporal_scope=boundary.temporal_scope,
            trust_basis="explicit_trust",
            provenance_requirements=boundary.provenance_requirements,
            reconstruction_requirements=boundary.reconstruction_requirements,
            constraints=boundary.constraints,
        )

        declarations = [
            {
                "declaration_id": "trust_001",
                "declaration_type": "trust_declaration",
                "truster_id": "governance",
                "trusted_id": "argopack",
                "trust_basis": "explicit",
                "scope": {
                    "actors": ["argopack"],
                    "operations": ["subprocess.run"],
                    "resources": ["python -m sas"],
                    "consequence_types": ["external_consequential"],
                },
                "constraints": ["timeout=30", "capture_output=True"],
                "is_active": True,
                "provenance_id": "prov_trust_001",
            }
        ]

        return AdjudicationContext(
            boundary=boundary,
            runtime_events=ArgopackScenarioBuilder.build_runtime_evidence(),
            static_hypotheses=ArgopackScenarioBuilder.build_static_evidence(),
            reconciliation_results=ArgopackScenarioBuilder.build_reconciliation_evidence(),
            authority_reconstructions=ArgopackScenarioBuilder.build_authority_reconstruction(),
            declarations=declarations,
            governance_policies=[],
        )

    @staticmethod
    def build_scenario_c_delegation() -> AdjudicationContext:
        """Scenario C: Explicit delegation."""
        boundary = ArgopackScenarioBuilder.build_boundary()
        boundary = AuthorityBoundary(
            boundary_id=boundary.boundary_id,
            source_domain=boundary.source_domain,
            destination_domain=boundary.destination_domain,
            actor=boundary.actor,
            consequence_type=boundary.consequence_type,
            resource=boundary.resource,
            operation=boundary.operation,
            temporal_scope=boundary.temporal_scope,
            delegation_source="governance",
            provenance_requirements=boundary.provenance_requirements,
            reconstruction_requirements=boundary.reconstruction_requirements,
            constraints=boundary.constraints,
        )

        declarations = [
            {
                "declaration_id": "deleg_001",
                "declaration_type": "delegation_declaration",
                "delegator_id": "governance",
                "delegate_id": "argopack",
                "scope": {
                    "actors": ["argopack"],
                    "operations": ["subprocess.run"],
                    "resources": ["python -m sas"],
                    "consequence_types": ["external_consequential"],
                },
                "constraints": ["timeout=30", "capture_output=True"],
                "is_active": True,
                "provenance_id": "prov_deleg_001",
            }
        ]

        return AdjudicationContext(
            boundary=boundary,
            runtime_events=ArgopackScenarioBuilder.build_runtime_evidence(),
            static_hypotheses=ArgopackScenarioBuilder.build_static_evidence(),
            reconciliation_results=ArgopackScenarioBuilder.build_reconciliation_evidence(),
            authority_reconstructions=ArgopackScenarioBuilder.build_authority_reconstruction(),
            declarations=declarations,
            governance_policies=[],
        )

    @staticmethod
    def build_scenario_d_prohibition() -> AdjudicationContext:
        """Scenario D: Explicit prohibition."""
        boundary = ArgopackScenarioBuilder.build_boundary()

        governance_policies = [
            {
                "policy_id": "policy_001",
                "name": "prohibit_argopack_subprocess",
                "prohibits": True,
                "actors": ["argopack"],
                "operations": ["subprocess.run"],
                "resources": ["python -m sas"],
                "provenance_id": "prov_policy_001",
            }
        ]

        return AdjudicationContext(
            boundary=boundary,
            runtime_events=ArgopackScenarioBuilder.build_runtime_evidence(),
            static_hypotheses=ArgopackScenarioBuilder.build_static_evidence(),
            reconciliation_results=ArgopackScenarioBuilder.build_reconciliation_evidence(),
            authority_reconstructions=ArgopackScenarioBuilder.build_authority_reconstruction(),
            declarations=[],
            governance_policies=governance_policies,
        )


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------


def run_argopack_adjudication() -> dict[str, Any]:
    """Run the Argopack adjudication scenarios."""
    builder = ArgopackScenarioBuilder()
    adjudicator = AuthorityBoundaryAdjudicator()

    scenarios = {
        "A_no_declaration": builder.build_scenario_a_no_declaration(),
        "B_trust_declaration": builder.build_scenario_b_trust_declaration(),
        "C_delegation": builder.build_scenario_c_delegation(),
        "D_prohibition": builder.build_scenario_d_prohibition(),
    }

    results = {}
    for name, context in scenarios.items():
        adjudication = adjudicator.adjudicate(context)
        results[name] = adjudication.to_dict()

    return {
        "scenarios": results,
        "summary": {
            "total_scenarios": len(scenarios),
            "classifications": {
                name: r["classification"]
                for name, r in results.items()
            },
            "governance_dispositions": {
                name: r["governance_disposition"]
                for name, r in results.items()
            },
        },
    }


if __name__ == "__main__":
    import json
    results = run_argopack_adjudication()
    print(json.dumps(results, indent=2))
