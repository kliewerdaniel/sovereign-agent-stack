"""Phase 31: Observed Effect → Authority Path Reconstruction.

Central question:
    When a consequential effect is observed at runtime, can the system
    independently reconstruct the authority path that governed that effect,
    and distinguish valid authorization from missing or invalid authority evidence?

The four fundamental outcomes:
    VALID_AUTHORITY_PATH      — complete valid path from trust anchor to effect
    INVALID_AUTHORITY_PATH     — path exists but violates rules
    AUTHORITY_PATH_INCOMPLETE  — some required evidence is missing
    AUTHORITY_PATH_UNKNOWN     — insufficient evidence to determine

Critical distinctions:
    OBSERVED ≠ AUTHORIZED
    AUTHORIZATION_ID ≠ AUTHORITY_PROOF
    CAPABILITY ≠ AUTHORITY
    VALID_CAPABILITY ≠ VALID_AUTHORITY_DERIVATION
    GOVERNANCE_DISPOSITION ≠ AUTHORITY
    MISSING_EVIDENCE ≠ INVALID_AUTHORITY
    NO_PATH_FOUND ≠ PATH_PROVEN_INVALID
    VALID_PATH_WITHIN_INCOMPLETE_GRAPH ≠ GLOBAL_AUTHORITY_VALID
    HISTORICALLY_VALID ≠ CURRENTLY_VALID
    RECONSTRUCTION ≠ AUTHORITY_CREATION
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Core enumerations
# ---------------------------------------------------------------------------


class PathValidity(str, Enum):
    """Validity classification of a reconstructed authority path."""
    VALID = "valid_authority_path"
    INVALID = "invalid_authority_path"
    INCOMPLETE = "authority_path_incomplete"
    UNKNOWN = "authority_path_unknown"


class PathNodeStatus(str, Enum):
    """Status of a single node in the reconstructed path."""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    MISSING = "missing"
    INVALID = "invalid"
    EXPIRED = "expired"
    FORGED = "forged"


class DelegationStatus(str, Enum):
    """Status of a delegation link."""
    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    EXPIRED = "expired"
    CYCLIC = "cyclic"
    UNDECLARED = "undeclared"
    UNRECOGNIZED_ANCHOR = "unrecognized_anchor"


class CapabilityStatus(str, Enum):
    """Status of a capability in the path."""
    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    UNVERIFIED = "unverified"
    LAUNDERED = "laundered"
    EXPIRED = "expired"
    SCOPE_MISMATCH = "scope_mismatch"


class GovernanceStatus(str, Enum):
    """Status of governance disposition."""
    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    UNVERIFIED = "unverified"
    LAUNDERED = "laundered"
    DISPOSITION_WITHOUT_AUTHORITY = "disposition_without_authority"


class TemporalStatus(str, Enum):
    """Temporal status of authority."""
    VALID = "valid"
    EXPIRED = "expired"
    NOT_YET_VALID = "not_yet_valid"
    HISTORICALLY_VALID = "historically_valid"
    CURRENTLY_VALID = "currently_valid"


class ScopeStatus(str, Enum):
    """Scope/domain status."""
    VALID = "valid"
    MISMATCH = "mismatch"
    CROSS_DOMAIN_BLOCKED = "cross_domain_blocked"
    WIDENED = "widened"


class AttributionStatus(str, Enum):
    """Attribution status for async execution."""
    CONFIRMED = "confirmed"
    UNKNOWN = "unknown"
    INVALID = "invalid"
    CALLER_TO_WORKER_UNCONFIRMED = "caller_to_worker_unconfirmed"


class EscapeType(str, Enum):
    """Type of authority escape."""
    NO_ESCAPE = "no_escape"
    DIRECT_PRIMITIVE_BYPASS = "direct_primitive_bypass"
    MISSING_RUNTIME_GATE = "missing_runtime_gate"
    MISSING_FILESYSTEM_BOUND = "missing_filesystem_bound"
    MISSING_DATABASE_BOUND = "missing_database_bound"
    MISSING_SUBPROCESS_BOUND = "missing_subprocess_bound"
    AUTHORIZATION_LAUNDERING = "authorization_laundering"
    CAPABILITY_LAUNDERING = "capability_laundering"
    GOVERNANCE_LAUNDERING = "governance_laundering"
    REPLAYED_RECEIPT = "replayed_receipt"
    CROSS_DOMAIN_MISMATCH = "cross_domain_mismatch"
    TEMPORAL_EXPIRED = "temporal_expired"
    CYCLIC_DELEGATION = "cyclic_delegation"
    UNDECLARED_DELEGATION = "undeclared_delegation"
    UNRECOGNIZED_ANCHOR = "unrecognized_anchor"


# ---------------------------------------------------------------------------
# Authority path node
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityPathNode:
    """A single node in a reconstructed authority path."""
    node_id: str
    node_type: str  # trust_anchor, delegation, policy, governance, capability, execution_gate, effect
    principal: str
    capability: str
    scope: str
    domain: str
    status: PathNodeStatus
    evidence_id: str
    evidence_type: str
    temporal_status: TemporalStatus
    scope_status: ScopeStatus
    provenance: str
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Reconstructed authority path — the core epistemic object
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReconstructedAuthorityPath:
    """A reconstructed authority path from trust anchor to observed effect.

    This is evidence about authority, not authority itself.
    The path is reconstructed from available provenance-bearing artifacts.

    Fields:
        path_id: unique identifier
        observation_id: the runtime observation this path explains
        effect_id: the effect being explained
        validity: overall validity classification
        nodes: ordered list of path nodes (trust anchor → effect)
        trust_anchor_id: the root trust anchor
        delegation_chain: delegation links in the path
        capability_status: status of the capability
        governance_status: status of governance disposition
        temporal_status: temporal validity status
        scope_status: scope/domain status
        attribution_status: attribution status for async execution
        escape_type: type of escape detected (if any)
        completeness_status: completeness of the authority graph
        provenance: lineage of the reconstruction
        confidence: confidence in the reconstruction (NOT a probability)
        notes: additional notes
        metadata: additional metadata
    """
    path_id: str
    observation_id: str
    effect_id: str
    validity: PathValidity
    nodes: tuple[AuthorityPathNode, ...]
    trust_anchor_id: str
    delegation_chain: tuple[str, ...]
    capability_status: CapabilityStatus
    governance_status: GovernanceStatus
    temporal_status: TemporalStatus
    scope_status: ScopeStatus
    attribution_status: AttributionStatus
    escape_type: EscapeType
    completeness_status: str
    provenance: str
    confidence: float
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        return self.validity == PathValidity.VALID

    @property
    def is_escape(self) -> bool:
        return self.escape_type != EscapeType.NO_ESCAPE

    @property
    def depth(self) -> int:
        return len(self.nodes)


# ---------------------------------------------------------------------------
# Reconstruction world
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReconstructionWorld:
    """An adversarial world for authority path reconstruction experiments.

    Contains:
        observation: the runtime effect observation
        true_authority_path: the actual authority path (oracle only)
        available_evidence: evidence available to the reconstruction engine
        ground_truth_validity: the true validity classification
        escape_type: the true escape type (if any)
    """
    world_id: str
    description: str
    observation_id: str
    effect_id: str
    effect_category: str
    effect_source: str
    effect_target: str
    true_authority_path: tuple[AuthorityPathNode, ...]
    available_evidence: tuple[str, ...]
    ground_truth_validity: PathValidity
    escape_type: EscapeType
    has_authorization_id: bool
    has_capability_id: bool
    has_governance_disposition: bool
    has_execution_receipt: bool
    has_provenance: bool
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Oracle evaluation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OracleEvaluation:
    """Independent oracle evaluation of a reconstructed authority path."""
    evaluation_id: str
    world_id: str
    reconstructed_validity: PathValidity
    true_validity: PathValidity
    validity_match: bool
    reconstructed_escape: EscapeType
    true_escape: EscapeType
    escape_match: bool
    false_authorization: bool  # Reconstructed as VALID but actually INVALID/ESCAPE
    false_escape: bool         # Reconstructed as ESCAPE but actually VALID
    missing_evidence_correct: bool  # Correctly identified as INCOMPLETE
    notes: str = ""


# ---------------------------------------------------------------------------
# Path reconstruction engine
# ---------------------------------------------------------------------------


class PathReconstructionEngine:
    """Reconstructs authority paths from runtime evidence.

    CRITICAL INVARIANTS:
        RECONSTRUCTION ≠ AUTHORITY_CREATION
        AUTHORITY_EVIDENCE ≠ AUTHORITY
        PATH_RECONSTRUCTION ≠ AUTHORITY_DELEGATION
        OBSERVATION ≠ AUTHORIZATION

    The engine derives the path only from artifacts available to the runtime system.
    It does NOT infer missing links merely because the final effect contains an authorization ID.
    """

    def __init__(self, engine_id: str):
        self.engine_id = engine_id
        self.reconstructions: list[ReconstructedAuthorityPath] = []

    def reconstruct(
        self,
        observation_id: str,
        effect_id: str,
        effect_category: str,
        effect_source: str,
        effect_target: str,
        available_evidence: tuple[str, ...],
        has_authorization_id: bool,
        has_capability_id: bool,
        has_governance_disposition: bool,
        has_execution_receipt: bool,
        has_provenance: bool,
        true_path: tuple[AuthorityPathNode, ...] | None = None,
    ) -> ReconstructedAuthorityPath:
        """Reconstruct an authority path from available evidence.

        The reconstruction is based on actual provenance-bearing artifacts.
        It does NOT use the true_path (which is oracle-only).
        """
        # Determine what evidence is present
        evidence_set = set(available_evidence)

        # Step 1: Check for trust anchor
        has_trust_anchor = "trust_anchor" in evidence_set
        has_delegation = "delegation" in evidence_set
        has_policy = "policy" in evidence_set
        has_governance = "governance" in evidence_set
        has_capability = "capability" in evidence_set
        has_execution_gate = "execution_gate" in evidence_set

        # Step 2: Build nodes based on available evidence
        nodes: list[AuthorityPathNode] = []

        # Trust anchor node
        if has_trust_anchor:
            nodes.append(AuthorityPathNode(
                node_id=f"node-{uuid.uuid4().hex[:8]}",
                node_type="trust_anchor",
                principal="admin",
                capability="*",
                scope="*",
                domain="default",
                status=PathNodeStatus.VERIFIED,
                evidence_id="trust_anchor_001",
                evidence_type="trust_anchor_record",
                temporal_status=TemporalStatus.VALID,
                scope_status=ScopeStatus.VALID,
                provenance=f"{self.engine_id}:trust_anchor",
            ))

        # Delegation node
        if has_delegation:
            nodes.append(AuthorityPathNode(
                node_id=f"node-{uuid.uuid4().hex[:8]}",
                node_type="delegation",
                principal="admin",
                capability="subprocess.execute",
                scope="runtime",
                domain="default",
                status=PathNodeStatus.VERIFIED,
                evidence_id="delegation_001",
                evidence_type="delegation_link",
                temporal_status=TemporalStatus.VALID,
                scope_status=ScopeStatus.VALID,
                provenance=f"{self.engine_id}:delegation",
            ))

        # Policy node
        if has_policy:
            nodes.append(AuthorityPathNode(
                node_id=f"node-{uuid.uuid4().hex[:8]}",
                node_type="policy",
                principal="admin",
                capability="subprocess.execute",
                scope="runtime",
                domain="default",
                status=PathNodeStatus.VERIFIED,
                evidence_id="policy_001",
                evidence_type="policy_record",
                temporal_status=TemporalStatus.VALID,
                scope_status=ScopeStatus.VALID,
                provenance=f"{self.engine_id}:policy",
            ))

        # Governance node
        if has_governance:
            nodes.append(AuthorityPathNode(
                node_id=f"node-{uuid.uuid4().hex[:8]}",
                node_type="governance",
                principal="admin",
                capability="subprocess.execute",
                scope="runtime",
                domain="default",
                status=PathNodeStatus.VERIFIED,
                evidence_id="governance_001",
                evidence_type="governance_disposition",
                temporal_status=TemporalStatus.VALID,
                scope_status=ScopeStatus.VALID,
                provenance=f"{self.engine_id}:governance",
            ))

        # Capability node
        if has_capability:
            nodes.append(AuthorityPathNode(
                node_id=f"node-{uuid.uuid4().hex[:8]}",
                node_type="capability",
                principal="admin",
                capability="subprocess.execute",
                scope="runtime",
                domain="default",
                status=PathNodeStatus.VERIFIED,
                evidence_id="capability_001",
                evidence_type="capability_record",
                temporal_status=TemporalStatus.VALID,
                scope_status=ScopeStatus.VALID,
                provenance=f"{self.engine_id}:capability",
            ))

        # Execution gate node
        if has_execution_gate:
            nodes.append(AuthorityPathNode(
                node_id=f"node-{uuid.uuid4().hex[:8]}",
                node_type="execution_gate",
                principal="admin",
                capability="subprocess.execute",
                scope="runtime",
                domain="default",
                status=PathNodeStatus.VERIFIED,
                evidence_id="execution_gate_001",
                evidence_type="execution_receipt",
                temporal_status=TemporalStatus.VALID,
                scope_status=ScopeStatus.VALID,
                provenance=f"{self.engine_id}:execution_gate",
            ))

        # Effect node (always present — this is what was observed)
        nodes.append(AuthorityPathNode(
            node_id=f"node-{uuid.uuid4().hex[:8]}",
            node_type="effect",
            principal="admin",
            capability=effect_target,
            scope="runtime",
            domain="default",
            status=PathNodeStatus.VERIFIED,
            evidence_id=effect_id,
            evidence_type="runtime_observation",
            temporal_status=TemporalStatus.VALID,
            scope_status=ScopeStatus.VALID,
            provenance=f"{self.engine_id}:effect",
        ))

        # Step 3: Determine validity based on evidence completeness
        validity = self._determine_validity(
            has_trust_anchor=has_trust_anchor,
            has_delegation=has_delegation,
            has_policy=has_policy,
            has_governance=has_governance,
            has_capability=has_capability,
            has_execution_gate=has_execution_gate,
            has_authorization_id=has_authorization_id,
            has_capability_id=has_capability_id,
            has_governance_disposition=has_governance_disposition,
            has_execution_receipt=has_execution_receipt,
            has_provenance=has_provenance,
            evidence_set=evidence_set,
        )

        # Step 4: Determine escape type
        escape_type = self._determine_escape_type(
            validity=validity,
            has_authorization_id=has_authorization_id,
            has_capability_id=has_capability_id,
            has_governance_disposition=has_governance_disposition,
            evidence_set=evidence_set,
        )

        # Step 5: Determine capability/governance/temporal/scope status
        capability_status = self._determine_capability_status(has_capability, has_capability_id, evidence_set)
        governance_status = self._determine_governance_status(has_governance, has_governance_disposition, evidence_set)
        temporal_status = self._determine_temporal_status(evidence_set)
        scope_status = self._determine_scope_status(evidence_set)
        attribution_status = self._determine_attribution_status(evidence_set)

        # Step 6: Build reconstruction
        reconstruction = ReconstructedAuthorityPath(
            path_id=f"path-{uuid.uuid4().hex[:12]}",
            observation_id=observation_id,
            effect_id=effect_id,
            validity=validity,
            nodes=tuple(nodes),
            trust_anchor_id="trust_anchor_001" if has_trust_anchor else "",
            delegation_chain=("delegation_001",) if has_delegation else (),
            capability_status=capability_status,
            governance_status=governance_status,
            temporal_status=temporal_status,
            scope_status=scope_status,
            attribution_status=attribution_status,
            escape_type=escape_type,
            completeness_status=self._determine_completeness(evidence_set),
            provenance=f"{self.engine_id}:{observation_id}",
            confidence=self._compute_confidence(validity, evidence_set),
            metadata={"engine_id": self.engine_id, "evidence_count": len(evidence_set)},
        )

        self.reconstructions.append(reconstruction)
        return reconstruction

    def _determine_validity(
        self,
        has_trust_anchor: bool,
        has_delegation: bool,
        has_policy: bool,
        has_governance: bool,
        has_capability: bool,
        has_execution_gate: bool,
        has_authorization_id: bool,
        has_capability_id: bool,
        has_governance_disposition: bool,
        has_execution_receipt: bool,
        has_provenance: bool,
        evidence_set: set[str],
    ) -> PathValidity:
        """Determine the validity of the reconstructed path."""
        # Check for invalidity indicators
        invalidity_indicators = {
            "invalid_delegation", "cyclic_delegation", "undeclared_delegation",
            "unrecognized_anchor", "expired_authority", "scope_mismatch",
            "wrong_actor", "forged_authorization", "replayed_receipt",
            "authorization_laundering", "capability_laundering",
            "governance_laundering", "cross_domain_mismatch",
            "disposition_without_authority", "temporal_expired",
        }
        if evidence_set & invalidity_indicators:
            return PathValidity.INVALID

        # Check for completeness
        required_evidence = {"trust_anchor", "delegation", "policy", "governance", "capability", "execution_gate"}
        present_required = required_evidence & evidence_set

        if present_required == required_evidence:
            return PathValidity.VALID
        elif len(present_required) >= 4:
            return PathValidity.INCOMPLETE
        else:
            return PathValidity.UNKNOWN

    def _determine_escape_type(
        self,
        validity: PathValidity,
        has_authorization_id: bool,
        has_capability_id: bool,
        has_governance_disposition: bool,
        evidence_set: set[str],
    ) -> EscapeType:
        """Determine the type of authority escape."""
        if validity == PathValidity.VALID:
            return EscapeType.NO_ESCAPE

        escape_indicators = {
            "direct_primitive_bypass": EscapeType.DIRECT_PRIMITIVE_BYPASS,
            "missing_runtime_gate": EscapeType.MISSING_RUNTIME_GATE,
            "missing_filesystem_bound": EscapeType.MISSING_FILESYSTEM_BOUND,
            "missing_database_bound": EscapeType.MISSING_DATABASE_BOUND,
            "missing_subprocess_bound": EscapeType.MISSING_SUBPROCESS_BOUND,
            "authorization_laundering": EscapeType.AUTHORIZATION_LAUNDERING,
            "forged_authorization": EscapeType.AUTHORIZATION_LAUNDERING,
            "capability_laundering": EscapeType.CAPABILITY_LAUNDERING,
            "governance_laundering": EscapeType.GOVERNANCE_LAUNDERING,
            "disposition_without_authority": EscapeType.GOVERNANCE_LAUNDERING,
            "replayed_receipt": EscapeType.REPLAYED_RECEIPT,
            "cross_domain_mismatch": EscapeType.CROSS_DOMAIN_MISMATCH,
            "temporal_expired": EscapeType.TEMPORAL_EXPIRED,
            "expired_authority": EscapeType.TEMPORAL_EXPIRED,
            "cyclic_delegation": EscapeType.CYCLIC_DELEGATION,
            "undeclared_delegation": EscapeType.UNDECLARED_DELEGATION,
            "unrecognized_anchor": EscapeType.UNRECOGNIZED_ANCHOR,
        }
        for indicator, escape_type in escape_indicators.items():
            if indicator in evidence_set:
                return escape_type

        return EscapeType.DIRECT_PRIMITIVE_BYPASS

    def _determine_capability_status(
        self, has_capability: bool, has_capability_id: bool, evidence_set: set[str]
    ) -> CapabilityStatus:
        if "capability_laundering" in evidence_set:
            return CapabilityStatus.LAUNDERED
        if "expired_capability" in evidence_set:
            return CapabilityStatus.EXPIRED
        if "scope_mismatch" in evidence_set:
            return CapabilityStatus.SCOPE_MISMATCH
        if has_capability:
            return CapabilityStatus.VALID
        if has_capability_id:
            return CapabilityStatus.UNVERIFIED
        return CapabilityStatus.MISSING

    def _determine_governance_status(
        self, has_governance: bool, has_governance_disposition: bool, evidence_set: set[str]
    ) -> GovernanceStatus:
        if "governance_laundering" in evidence_set:
            return GovernanceStatus.LAUNDERED
        if "disposition_without_authority" in evidence_set:
            return GovernanceStatus.DISPOSITION_WITHOUT_AUTHORITY
        if has_governance:
            return GovernanceStatus.VALID
        if has_governance_disposition:
            return GovernanceStatus.UNVERIFIED
        return GovernanceStatus.MISSING

    def _determine_temporal_status(self, evidence_set: set[str]) -> TemporalStatus:
        if "expired_authority" in evidence_set:
            return TemporalStatus.EXPIRED
        if "not_yet_valid" in evidence_set:
            return TemporalStatus.NOT_YET_VALID
        if "historically_valid" in evidence_set:
            return TemporalStatus.HISTORICALLY_VALID
        return TemporalStatus.VALID

    def _determine_scope_status(self, evidence_set: set[str]) -> ScopeStatus:
        if "scope_mismatch" in evidence_set:
            return ScopeStatus.MISMATCH
        if "cross_domain_mismatch" in evidence_set:
            return ScopeStatus.CROSS_DOMAIN_BLOCKED
        if "scope_widened" in evidence_set:
            return ScopeStatus.WIDENED
        return ScopeStatus.VALID

    def _determine_attribution_status(self, evidence_set: set[str]) -> AttributionStatus:
        if "attribution_confirmed" in evidence_set:
            return AttributionStatus.CONFIRMED
        if "attribution_invalid" in evidence_set:
            return AttributionStatus.INVALID
        if "async_execution" in evidence_set:
            return AttributionStatus.CALLER_TO_WORKER_UNCONFIRMED
        return AttributionStatus.UNKNOWN

    def _determine_completeness(self, evidence_set: set[str]) -> str:
        required = {"trust_anchor", "delegation", "policy", "governance", "capability", "execution_gate"}
        present = required & evidence_set
        if present == required:
            return "complete_within_declared_graph"
        elif len(present) >= 4:
            return "incomplete"
        else:
            return "unknown"

    def _compute_confidence(self, validity: PathValidity, evidence_set: set[str]) -> float:
        """Compute confidence in the reconstruction.

        Confidence is NOT a probability of correctness.
        It is a measure of evidence sufficiency.
        """
        if validity == PathValidity.VALID:
            return 0.9
        elif validity == PathValidity.INCOMPLETE:
            return 0.5
        elif validity == PathValidity.INVALID:
            return 0.7
        else:
            return 0.2


# ---------------------------------------------------------------------------
# Independent oracle
# ---------------------------------------------------------------------------


class IndependentOracle:
    """Evaluates reconstructed authority paths against ground truth.

    The oracle knows the true authority path but the reconstruction engine does not.
    """

    def evaluate(
        self,
        world: ReconstructionWorld,
        reconstruction: ReconstructedAuthorityPath,
    ) -> OracleEvaluation:
        """Evaluate a reconstruction against ground truth."""
        validity_match = reconstruction.validity == world.ground_truth_validity
        escape_match = reconstruction.escape_type == world.escape_type

        # False authorization: reconstructed as VALID but actually INVALID/ESCAPE
        false_authorization = (
            reconstruction.validity == PathValidity.VALID
            and world.ground_truth_validity in (PathValidity.INVALID, PathValidity.UNKNOWN)
        )

        # False escape: reconstructed as ESCAPE but actually VALID
        false_escape = (
            reconstruction.escape_type != EscapeType.NO_ESCAPE
            and world.escape_type == EscapeType.NO_ESCAPE
        )

        # Missing evidence correctly identified
        missing_evidence_correct = (
            reconstruction.validity == PathValidity.INCOMPLETE
            and world.ground_truth_validity == PathValidity.INCOMPLETE
        )

        return OracleEvaluation(
            evaluation_id=f"eval-{uuid.uuid4().hex[:12]}",
            world_id=world.world_id,
            reconstructed_validity=reconstruction.validity,
            true_validity=world.ground_truth_validity,
            validity_match=validity_match,
            reconstructed_escape=reconstruction.escape_type,
            true_escape=world.escape_type,
            escape_match=escape_match,
            false_authorization=false_authorization,
            false_escape=false_escape,
            missing_evidence_correct=missing_evidence_correct,
        )


# ---------------------------------------------------------------------------
# Adversarial world generator
# ---------------------------------------------------------------------------


class AdversarialWorldGenerator:
    """Generates 20 adversarial worlds for Phase 31."""

    def generate_all_worlds(self) -> list[ReconstructionWorld]:
        return [
            self._world_01_complete_valid_path(),
            self._world_02_valid_path_missing_provenance(),
            self._world_03_valid_path_expired_temporal(),
            self._world_04_valid_path_wrong_scope(),
            self._world_05_valid_path_wrong_actor(),
            self._world_06_valid_capability_invalid_upstream(),
            self._world_07_valid_governance_missing_authority(),
            self._world_08_valid_authority_missing_capability(),
            self._world_09_capability_not_from_authority(),
            self._world_10_direct_primitive_bypass(),
            self._world_11_forged_authorization(),
            self._world_12_replayed_receipt(),
            self._world_13_cross_domain_mismatch(),
            self._world_14_undeclared_delegation(),
            self._world_15_cyclic_delegation(),
            self._world_16_unrecognized_anchor(),
            self._world_17_emergency_execution(),
            self._world_18_recovery_execution(),
            self._world_19_background_incomplete_attribution(),
            self._world_20_no_authority_evidence(),
        ]

    def _make_node(
        self,
        node_type: str,
        principal: str,
        capability: str,
        scope: str = "runtime",
        domain: str = "default",
        status: PathNodeStatus = PathNodeStatus.VERIFIED,
        evidence_id: str = "",
        evidence_type: str = "",
        temporal_status: TemporalStatus = TemporalStatus.VALID,
        scope_status: ScopeStatus = ScopeStatus.VALID,
        provenance: str = "",
    ) -> AuthorityPathNode:
        return AuthorityPathNode(
            node_id=f"node-{uuid.uuid4().hex[:8]}",
            node_type=node_type,
            principal=principal,
            capability=capability,
            scope=scope,
            domain=domain,
            status=status,
            evidence_id=evidence_id or f"ev-{uuid.uuid4().hex[:8]}",
            evidence_type=evidence_type or node_type,
            temporal_status=temporal_status,
            scope_status=scope_status,
            provenance=provenance or f"oracle:{node_type}",
        )

    def _world_01_complete_valid_path(self) -> ReconstructionWorld:
        """1. Complete valid authority path."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_01_complete_valid_path",
            description="Complete valid authority path from trust anchor to effect",
            observation_id="obs_01",
            effect_id="eff_01",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate",
            ),
            ground_truth_validity=PathValidity.VALID,
            escape_type=EscapeType.NO_ESCAPE,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_02_valid_path_missing_provenance(self) -> ReconstructionWorld:
        """2. Valid path with missing provenance."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_02_valid_path_missing_provenance",
            description="Valid path but provenance record is missing",
            observation_id="obs_02",
            effect_id="eff_02",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate",
            ),
            ground_truth_validity=PathValidity.INCOMPLETE,
            escape_type=EscapeType.NO_ESCAPE,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=False,  # Missing provenance
        )

    def _world_03_valid_path_expired_temporal(self) -> ReconstructionWorld:
        """3. Valid path with expired temporal authority."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute",
                           temporal_status=TemporalStatus.EXPIRED),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_03_valid_path_expired_temporal",
            description="Valid path but authority expired before execution",
            observation_id="obs_03",
            effect_id="eff_03",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "expired_authority",
            ),
            ground_truth_validity=PathValidity.INVALID,
            escape_type=EscapeType.TEMPORAL_EXPIRED,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_04_valid_path_wrong_scope(self) -> ReconstructionWorld:
        """4. Valid path with wrong scope."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute",
                           scope_status=ScopeStatus.MISMATCH),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_04_valid_path_wrong_scope",
            description="Valid path but authority scope is production, effect is staging",
            observation_id="obs_04",
            effect_id="eff_04",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "scope_mismatch",
            ),
            ground_truth_validity=PathValidity.INVALID,
            escape_type=EscapeType.DIRECT_PRIMITIVE_BYPASS,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_05_valid_path_wrong_actor(self) -> ReconstructionWorld:
        """5. Valid path with wrong actor."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "other-actor", "subprocess.execute"),
            self._make_node("effect", "other-actor", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_05_valid_path_wrong_actor",
            description="Valid path but actor mismatch",
            observation_id="obs_05",
            effect_id="eff_05",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "wrong_actor",
            ),
            ground_truth_validity=PathValidity.INVALID,
            escape_type=EscapeType.DIRECT_PRIMITIVE_BYPASS,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_06_valid_capability_invalid_upstream(self) -> ReconstructionWorld:
        """6. Valid capability but invalid upstream authority."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute",
                           status=PathNodeStatus.INVALID),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_06_valid_capability_invalid_upstream",
            description="Valid capability but invalid upstream authority",
            observation_id="obs_06",
            effect_id="eff_06",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "invalid_delegation",
            ),
            ground_truth_validity=PathValidity.INVALID,
            escape_type=EscapeType.DIRECT_PRIMITIVE_BYPASS,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_07_valid_governance_missing_authority(self) -> ReconstructionWorld:
        """7. Valid governance disposition but missing authority transition."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute",
                           status=PathNodeStatus.MISSING),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_07_valid_governance_missing_authority",
            description="Valid governance but missing authority transition",
            observation_id="obs_07",
            effect_id="eff_07",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "execution_gate", "disposition_without_authority",
            ),
            ground_truth_validity=PathValidity.INVALID,
            escape_type=EscapeType.GOVERNANCE_LAUNDERING,
            has_authorization_id=True,
            has_capability_id=False,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_08_valid_authority_missing_capability(self) -> ReconstructionWorld:
        """8. Valid authority but missing capability."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute",
                           status=PathNodeStatus.MISSING),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_08_valid_authority_missing_capability",
            description="Valid authority but missing capability",
            observation_id="obs_08",
            effect_id="eff_08",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "execution_gate",
            ),
            ground_truth_validity=PathValidity.INCOMPLETE,
            escape_type=EscapeType.NO_ESCAPE,
            has_authorization_id=True,
            has_capability_id=False,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_09_capability_not_from_authority(self) -> ReconstructionWorld:
        """9. Capability exists but does not derive from the authority path."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute",
                           status=PathNodeStatus.INVALID),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_09_capability_not_from_authority",
            description="Capability exists but does not derive from authority path",
            observation_id="obs_09",
            effect_id="eff_09",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "capability_laundering",
            ),
            ground_truth_validity=PathValidity.INVALID,
            escape_type=EscapeType.CAPABILITY_LAUNDERING,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_10_direct_primitive_bypass(self) -> ReconstructionWorld:
        """10. Direct primitive bypass."""
        nodes = (
            self._make_node("effect", "admin", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_10_direct_primitive_bypass",
            description="Direct primitive bypass — no authority path",
            observation_id="obs_10",
            effect_id="eff_10",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=("direct_primitive_bypass",),
            ground_truth_validity=PathValidity.INVALID,
            escape_type=EscapeType.DIRECT_PRIMITIVE_BYPASS,
            has_authorization_id=False,
            has_capability_id=False,
            has_governance_disposition=False,
            has_execution_receipt=False,
            has_provenance=False,
        )

    def _world_11_forged_authorization(self) -> ReconstructionWorld:
        """11. Forged authorization ID."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_11_forged_authorization",
            description="Forged authorization ID — auth_001 does not derive from authority graph",
            observation_id="obs_11",
            effect_id="eff_11",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "forged_authorization",
            ),
            ground_truth_validity=PathValidity.INVALID,
            escape_type=EscapeType.AUTHORIZATION_LAUNDERING,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_12_replayed_receipt(self) -> ReconstructionWorld:
        """12. Replayed execution receipt."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_12_replayed_receipt",
            description="Replayed execution receipt from T1 used at T2",
            observation_id="obs_12",
            effect_id="eff_12",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "replayed_receipt",
            ),
            ground_truth_validity=PathValidity.INVALID,
            escape_type=EscapeType.REPLAYED_RECEIPT,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_13_cross_domain_mismatch(self) -> ReconstructionWorld:
        """13. Cross-domain authority mismatch."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute",
                           scope_status=ScopeStatus.CROSS_DOMAIN_BLOCKED),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_13_cross_domain_mismatch",
            description="Authority domain is DOMAIN_A, effect domain is DOMAIN_B",
            observation_id="obs_13",
            effect_id="eff_13",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "cross_domain_mismatch",
            ),
            ground_truth_validity=PathValidity.INVALID,
            escape_type=EscapeType.CROSS_DOMAIN_MISMATCH,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_14_undeclared_delegation(self) -> ReconstructionWorld:
        """14. Authority path containing an undeclared delegation."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute",
                           status=PathNodeStatus.INVALID),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_14_undeclared_delegation",
            description="Authority path contains an undeclared delegation",
            observation_id="obs_14",
            effect_id="eff_14",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "undeclared_delegation",
            ),
            ground_truth_validity=PathValidity.INVALID,
            escape_type=EscapeType.UNDECLARED_DELEGATION,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_15_cyclic_delegation(self) -> ReconstructionWorld:
        """15. Authority path containing a cyclic delegation."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute",
                           status=PathNodeStatus.INVALID),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_15_cyclic_delegation",
            description="Authority path contains a cyclic delegation A→B→A",
            observation_id="obs_15",
            effect_id="eff_15",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "cyclic_delegation",
            ),
            ground_truth_validity=PathValidity.INVALID,
            escape_type=EscapeType.CYCLIC_DELEGATION,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_16_unrecognized_anchor(self) -> ReconstructionWorld:
        """16. Authority path terminating at an unrecognized anchor."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*",
                           status=PathNodeStatus.INVALID),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_16_unrecognized_anchor",
            description="Authority path terminates at an unrecognized anchor",
            observation_id="obs_16",
            effect_id="eff_16",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "unrecognized_anchor",
            ),
            ground_truth_validity=PathValidity.INVALID,
            escape_type=EscapeType.UNRECOGNIZED_ANCHOR,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_17_emergency_execution(self) -> ReconstructionWorld:
        """17. Emergency execution with a distinct legitimate authority path."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "emergency.execute"),
            self._make_node("policy", "admin", "emergency.execute"),
            self._make_node("governance", "admin", "emergency.execute"),
            self._make_node("capability", "admin", "emergency.execute"),
            self._make_node("execution_gate", "admin", "emergency.execute"),
            self._make_node("effect", "admin", "os.system"),
        )
        return ReconstructionWorld(
            world_id="world_17_emergency_execution",
            description="Emergency execution with distinct legitimate authority path",
            observation_id="obs_17",
            effect_id="eff_17",
            effect_category="subprocess",
            effect_source="src/sas/quant/emergency.py",
            effect_target="os.system",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate",
            ),
            ground_truth_validity=PathValidity.VALID,
            escape_type=EscapeType.NO_ESCAPE,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_18_recovery_execution(self) -> ReconstructionWorld:
        """18. Recovery execution with a distinct legitimate authority path."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "recovery.execute"),
            self._make_node("policy", "admin", "recovery.execute"),
            self._make_node("governance", "admin", "recovery.execute"),
            self._make_node("capability", "admin", "recovery.execute"),
            self._make_node("execution_gate", "admin", "recovery.execute"),
            self._make_node("effect", "admin", "subprocess.Popen"),
        )
        return ReconstructionWorld(
            world_id="world_18_recovery_execution",
            description="Recovery execution with distinct legitimate authority path",
            observation_id="obs_18",
            effect_id="eff_18",
            effect_category="subprocess",
            effect_source="src/sas/quant/recovery.py",
            effect_target="subprocess.Popen",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate",
            ),
            ground_truth_validity=PathValidity.VALID,
            escape_type=EscapeType.NO_ESCAPE,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_19_background_incomplete_attribution(self) -> ReconstructionWorld:
        """19. Background execution with incomplete caller attribution."""
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "worker", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_19_background_incomplete_attribution",
            description="Background execution with incomplete caller attribution",
            observation_id="obs_19",
            effect_id="eff_19",
            effect_category="subprocess",
            effect_source="src/sas/quant/background.py",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "async_execution",
            ),
            ground_truth_validity=PathValidity.INCOMPLETE,
            escape_type=EscapeType.NO_ESCAPE,
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )

    def _world_20_no_authority_evidence(self) -> ReconstructionWorld:
        """20. Observed external effect with no authority evidence at all."""
        nodes = (
            self._make_node("effect", "unknown", "subprocess.run"),
        )
        return ReconstructionWorld(
            world_id="world_20_no_authority_evidence",
            description="Observed external effect with no authority evidence at all",
            observation_id="obs_20",
            effect_id="eff_20",
            effect_category="subprocess",
            effect_source="unknown",
            effect_target="subprocess.run",
            true_authority_path=nodes,
            available_evidence=(),
            ground_truth_validity=PathValidity.UNKNOWN,
            escape_type=EscapeType.DIRECT_PRIMITIVE_BYPASS,
            has_authorization_id=False,
            has_capability_id=False,
            has_governance_disposition=False,
            has_execution_receipt=False,
            has_provenance=False,
        )


# ---------------------------------------------------------------------------
# Phase 31 experiment
# ---------------------------------------------------------------------------


class Phase31Experiment:
    """Runs the full Phase 31 experiment suite."""

    def __init__(self):
        self.worlds = AdversarialWorldGenerator().generate_all_worlds()
        self.engine = PathReconstructionEngine("phase31_engine")
        self.oracle = IndependentOracle()
        self.evaluations: list[OracleEvaluation] = []

    def run_all(self) -> dict[str, Any]:
        """Run all worlds and return summary."""
        for world in self.worlds:
            self._run_world(world)
        return self.summary()

    def _run_world(self, world: ReconstructionWorld) -> None:
        """Run a single world through the reconstruction engine."""
        reconstruction = self.engine.reconstruct(
            observation_id=world.observation_id,
            effect_id=world.effect_id,
            effect_category=world.effect_category,
            effect_source=world.effect_source,
            effect_target=world.effect_target,
            available_evidence=world.available_evidence,
            has_authorization_id=world.has_authorization_id,
            has_capability_id=world.has_capability_id,
            has_governance_disposition=world.has_governance_disposition,
            has_execution_receipt=world.has_execution_receipt,
            has_provenance=world.has_provenance,
        )
        self.evaluations.append(self.oracle.evaluate(world, reconstruction))

    def summary(self) -> dict[str, Any]:
        """Generate experiment summary."""
        valid_count = sum(1 for e in self.evaluations if e.validity_match)
        false_auth = sum(1 for e in self.evaluations if e.false_authorization)
        false_escape = sum(1 for e in self.evaluations if e.false_escape)
        escape_match = sum(1 for e in self.evaluations if e.escape_match)

        return {
            "total_worlds": len(self.worlds),
            "total_reconstructions": len(self.engine.reconstructions),
            "validity_matches": valid_count,
            "escape_matches": escape_match,
            "false_authorizations": false_auth,
            "false_escapes": false_escape,
            "validity_accuracy": valid_count / len(self.worlds) if self.worlds else 0,
            "escape_accuracy": escape_match / len(self.worlds) if self.worlds else 0,
        }
