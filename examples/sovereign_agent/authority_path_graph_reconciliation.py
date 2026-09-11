"""Phase 32: Reconstructed Authority Path → Declared Authority Graph Reconciliation.

Central research question:
    Can the system independently reconcile an authority path reconstructed from
    an observed runtime effect against the declared authority graph, and
    distinguish legitimate correspondence from graph divergence, incomplete
    knowledge, and genuine authority escape?

The three graph model:
    1. DECLARED AUTHORITY GRAPH — what the architecture claims
    2. OBSERVED EFFECT GRAPH — what actually happened at runtime
    3. EFFECTIVE AUTHORITY GRAPH — the path reconstructed from runtime evidence

The fundamental experiment:
    OBSERVED EFFECT
    → RUNTIME EVIDENCE
    → RECONSTRUCTED AUTHORITY PATH
    → DECLARED AUTHORITY GRAPH RECONCILIATION
    → EFFECTIVE AUTHORITY GRAPH
    → EPISTEMIC DISPOSITION

Critical distinctions:
    RECONSTRUCTION ≠ AUTHORIZATION
    RECONCILIATION ≠ AUTHORIZATION
    OBSERVED EFFECT ≠ AUTHORITY PROOF
    DECLARED AUTHORITY ≠ EFFECTIVE AUTHORITY
    DECLARED PATH ≠ RECONSTRUCTED PATH
    RECONSTRUCTED PATH ≠ TRUE PATH
    VALID PATH ≠ GLOBAL AUTHORITY VALIDITY
    MISSING CORRESPONDENCE ≠ INVALID AUTHORITY
    NO PATH FOUND ≠ PATH PROVEN INVALID
    INCOMPLETE GRAPH ≠ INVALID PATH
    INCOMPLETE GRAPH ≠ GLOBAL VALIDITY
    VALID PATH WITHIN INCOMPLETE GRAPH ≠ GLOBAL AUTHORITY VALID
    AUTHORIZATION_ID ≠ AUTHORITY_PROOF
    CAPABILITY ≠ AUTHORITY
    VALID_CAPABILITY ≠ VALID_AUTHORITY_DERIVATION
    GOVERNANCE_DISPOSITION ≠ AUTHORIZATION
    OBSERVATION ≠ AUTHORITY
    RUNTIME MAY MATERIALIZE AUTHORITY, NEVER CREATE AUTHORITY
    HISTORICALLY_VALID ≠ CURRENTLY_VALID
    VALID_AT_EXECUTION ≠ VALID_NOW
    CALLER_AUTHORITY ≠ WORKER_AUTHORITY
    CROSS_DOMAIN_OBSERVATION ≠ CROSS_DOMAIN_AUTHORITY
    EMERGENCY_PATH ≠ AUTOMATICALLY_UNAUTHORIZED
    RECOVERY_PATH ≠ AUTOMATICALLY_UNAUTHORIZED
    POLICY_EFFECT ≠ AUTHORITY
    AUTHORITY_GRAPH_COMPLETENESS ≠ AUTHORITY_PATH_VALIDITY
    AUTHORITY_PATH_VALIDITY ≠ AUTHORITY_GRAPH_COMPLETENESS
    STATIC POSSIBILITY ≠ EXECUTED EFFECT
    DECLARED AUTHORIZATION POSSIBILITY ≠ RUNTIME AUTHORITY PROOF

Existing infrastructure reused:
    - AuthorityGraph, AuthorityGraphNode, AuthoritySourceType (authority_genesis.py)
    - TrustAnchor, AuthorityDomain, TerminatedDelegationChain (trust_anchor.py)
    - PathReconstructionEngine, ReconstructedAuthorityPath (authority_path_reconstruction.py)
    - AuthorityRootRecord, DelegationChain, DelegationLink (authority_root.py)
    - AuthoritySurface, AuthorityEnvelope (effect_boundary.py)
    - AuthorityClaimWithProvenance (authority_under_uncertainty.py)
    - CompletenessClaim, CompletenessStatus (continuous_effect_reconciliation.py)
    - ObservableAuthorityMechanism, CompletenessDimension (authority_graph_completeness.py)
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


class CorrespondenceStatus(str, Enum):
    """Status of the correspondence between a reconstructed path and the
    declared authority graph.

    This is NOT an authorization status. It is an epistemic classification
    of the relationship between two representations.
    """
    CORRESPONDS = "corresponds"
    CORRESPONDS_WITH_INCOMPLETE_DECLARED_GRAPH = "corresponds_with_incomplete_declared_graph"
    DIVERGES = "diverges"
    INCOMPLETE = "incomplete"
    UNKNOWN = "unknown"
    INVALID_RECONSTRUCTION = "invalid_reconstruction"
    AUTHORITY_ESCAPE = "authority_escape"
    NO_DECLARED_CORRESPONDENCE_FOUND = "no_declared_correspondence_found"


class DivergenceType(str, Enum):
    """Type of divergence between declared and reconstructed paths."""
    NONE = "none"
    NODE_MISMATCH = "node_mismatch"
    EDGE_MISMATCH = "edge_mismatch"
    PROVENANCE_MISMATCH = "provenance_mismatch"
    TEMPORAL_MISMATCH = "temporal_mismatch"
    SCOPE_MISMATCH = "scope_mismatch"
    DOMAIN_MISMATCH = "domain_mismatch"
    ACTOR_MISMATCH = "actor_mismatch"
    CAPABILITY_DERIVATION_MISMATCH = "capability_derivation_mismatch"
    GOVERNANCE_MISMATCH = "governance_mismatch"
    TRUST_ANCHOR_MISMATCH = "trust_anchor_mismatch"
    DELEGATION_MISMATCH = "delegation_mismatch"
    UNDECLARED_INTERMEDIATE = "undeclared_intermediate"
    MULTIPLE_PATH_AMBIGUITY = "multiple_path_ambiguity"
    HISTORICALLY_VALID_NOW_EXPIRED = "historically_valid_now_expired"
    VALID_AT_EXECUTION_INVALID_NOW = "valid_at_execution_invalid_now"
    REPLAYED_AUTHORIZATION = "replayed_authorization"
    LAUNDERED_AUTHORIZATION = "laundered_authorization"
    LAUNDERED_CAPABILITY = "laundered_capability"
    LAUNDERED_GOVERNANCE = "laundered_governance"
    CYCLIC_DECLARED_GRAPH = "cyclic_declared_graph"
    INCOMPLETE_GRAPH_EXPLAINS_DIVERGENCE = "incomplete_graph_explains_divergence"
    NO_DECLARED_CORRESPONDENCE = "no_declared_correspondence"
    STATIC_POSSIBILITY_NOT_EXECUTED = "static_possibility_not_executed"
    UNKNOWN = "unknown"


class EpistemicStatus(str, Enum):
    """Epistemic status of the reconciliation result."""
    RECONCILED = "reconciled"
    RECONCILED_WITH_INCOMPLETE_DECLARED_GRAPH = "reconciled_with_incomplete_declared_graph"
    DIVERGENT = "divergent"
    INCOMPLETE = "incomplete"
    UNKNOWN = "unknown"
    INVALID_RECONSTRUCTION = "invalid_reconstruction"
    AUTHORITY_ESCAPE = "authority_escape"


class TemporalReconciliationStatus(str, Enum):
    """Temporal reconciliation status."""
    VALID_AT_EXECUTION_AND_CURRENT = "valid_at_execution_and_current"
    VALID_AT_EXECUTION_EXPIRED_NOW = "valid_at_execution_expired_now"
    HISTORICALLY_VALID = "historically_valid"
    NOT_YET_VALID = "not_yet_valid"
    EXPIRED_BEFORE_EXECUTION = "expired_before_execution"
    TEMPORAL_MISMATCH = "temporal_mismatch"
    UNKNOWN = "unknown"


class ScopeReconciliationStatus(str, Enum):
    """Scope reconciliation status."""
    MATCHING = "matching"
    EFFECT_BROADER = "effect_broader"
    EFFECT_NARROWER = "effect_narrower"
    SCOPE_MISMATCH = "scope_mismatch"
    UNKNOWN = "unknown"


class DomainReconciliationStatus(str, Enum):
    """Domain reconciliation status."""
    MATCHING = "matching"
    CROSS_DOMAIN_BLOCKED = "cross_domain_blocked"
    CROSS_DOMAIN_DELEGATED = "cross_domain_delegated"
    DOMAIN_MISMATCH = "domain_mismatch"
    UNKNOWN = "unknown"


class ActorReconciliationStatus(str, Enum):
    """Actor reconciliation status."""
    MATCHING = "matching"
    CALLER_TO_WORKER_UNCONFIRMED = "caller_to_worker_unconfirmed"
    ACTOR_MISMATCH = "actor_mismatch"
    EMERGENCY_ACTOR_VALID = "emergency_actor_valid"
    RECOVERY_ACTOR_VALID = "recovery_actor_valid"
    UNKNOWN = "unknown"


class GraphCompletenessStatus(str, Enum):
    """Completeness status of the declared authority graph."""
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    UNKNOWN = "unknown"
    COMPLETE_FOR_SCOPE = "complete_for_scope"
    INCOMPLETE_FOR_SCOPE = "incomplete_for_scope"


# ---------------------------------------------------------------------------
# Authority path node (reconstructed)
# ---------------------------------------------------------------------------


class AuthoritySourceType(str, Enum):
    """Type of authority source."""
    TRUST_ANCHOR = "trust_anchor"
    DELEGATION = "delegation"
    POLICY = "policy"
    IMPLICIT = "implicit"
    UNKNOWN = "unknown"


class PathNodeStatus(str, Enum):
    """Status of a single node in the reconstructed path."""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    MISSING = "missing"
    INVALID = "invalid"
    EXPIRED = "expired"
    FORGED = "forged"


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


class PathValidity(str, Enum):
    """Validity classification of a reconstructed authority path."""
    VALID = "valid_authority_path"
    INVALID = "invalid_authority_path"
    INCOMPLETE = "authority_path_incomplete"
    UNKNOWN = "authority_path_unknown"


@dataclass(frozen=True)
class AuthorityPathNode:
    """A single node in a reconstructed authority path."""
    node_id: str
    node_type: str
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


@dataclass(frozen=True)
class ReconstructedAuthorityPath:
    """A reconstructed authority path from trust anchor to observed effect.

    This is evidence about authority, not authority itself.
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
# Declared authority graph primitives
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeclaredAuthorityNode:
    """A node in the declared authority graph."""
    node_id: str
    node_type: str  # trust_anchor, delegation, policy, governance, capability, execution_gate
    principal: str
    capability: str
    scope: str
    domain: str
    source_type: AuthoritySourceType
    trust_anchor_id: str = ""
    outgoing_edges: tuple[str, ...] = ()
    incoming_edges: tuple[str, ...] = ()
    is_implicit: bool = False
    temporal_valid_from: str = "unbounded"
    temporal_valid_until: str = "unbounded"
    provenance: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeclaredAuthorityEdge:
    """An edge in the declared authority graph."""
    edge_id: str
    source_node_id: str
    target_node_id: str
    delegation_capability: str = ""
    delegation_scope: str = ""
    is_terminal: bool = False
    delegation_right: bool = False
    provenance: str = ""


@dataclass
class DeclaredAuthorityGraph:
    """The declared authority graph — what the architecture claims."""
    graph_id: str
    nodes: dict[str, DeclaredAuthorityNode] = field(default_factory=dict)
    edges: dict[str, DeclaredAuthorityEdge] = field(default_factory=dict)
    trust_anchor_ids: set[str] = field(default_factory=set)
    version: str = "v1"
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: DeclaredAuthorityNode) -> None:
        self.nodes[node.node_id] = node
        if node.source_type == AuthoritySourceType.TRUST_ANCHOR:
            self.trust_anchor_ids.add(node.node_id)

    def add_edge(self, edge: DeclaredAuthorityEdge) -> None:
        self.edges[edge.edge_id] = edge

    def get_node(self, node_id: str) -> DeclaredAuthorityNode | None:
        return self.nodes.get(node_id)

    def get_outgoing_edges(self, node_id: str) -> list[DeclaredAuthorityEdge]:
        return [e for e in self.edges.values() if e.source_node_id == node_id]

    def get_incoming_edges(self, node_id: str) -> list[DeclaredAuthorityEdge]:
        return [e for e in self.edges.values() if e.target_node_id == node_id]

    def detect_cycles(self) -> list[list[str]]:
        """Detect all cycles in the graph using DFS."""
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node_id: str, path: list[str]) -> None:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            for edge in self.get_outgoing_edges(node_id):
                if edge.target_node_id not in visited:
                    dfs(edge.target_node_id, path.copy())
                elif edge.target_node_id in rec_stack:
                    cycle_start = path.index(edge.target_node_id)
                    cycle = path[cycle_start:] + [edge.target_node_id]
                    cycles.append(cycle)
            rec_stack.discard(node_id)

        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id, [])
        return cycles

    def find_path_to_anchor(self, node_id: str) -> list[str] | None:
        """Find a path from a node back to a trust anchor."""
        if node_id in self.trust_anchor_ids:
            return [node_id]
        for edge in self.get_incoming_edges(node_id):
            path = self.find_path_to_anchor(edge.source_node_id)
            if path is not None:
                return path + [node_id]
        return None

    @property
    def is_acyclic(self) -> bool:
        return len(self.detect_cycles()) == 0


# ---------------------------------------------------------------------------
# Authority reconciliation — the core epistemic object
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityReconciliation:
    """The result of reconciling a reconstructed authority path against
    the declared authority graph.

    This is NOT an authorization. It is an epistemic claim about the
    correspondence between two representations.

    Fields preserve the full epistemic context:
        reconciliation_id: unique identifier
        effect_id: the observed effect being explained
        observation_id: the runtime observation
        reconstructed_path_id: the path being reconciled
        declared_graph_version: which version of the declared graph
        declared_path_reference: the matching declared path (if any)
        effective_path_reference: the reconstructed path
        correspondence_status: overall correspondence classification
        node_correspondence: whether nodes match
        edge_correspondence: whether edges match
        provenance_correspondence: whether provenance matches
        temporal_correspondence: temporal reconciliation status
        scope_correspondence: scope reconciliation status
        domain_correspondence: domain reconciliation status
        actor_correspondence: actor reconciliation status
        capability_correspondence: whether capability derivation matches
        governance_correspondence: whether governance matches
        trust_anchor_correspondence: whether trust anchor matches
        delegation_correspondence: whether delegation chain matches
        graph_completeness_status: completeness of the declared graph
        divergence_type: type of divergence (if any)
        epistemic_status: overall epistemic classification
        historical_validity: whether the path was historically valid
        current_validity: whether the path is currently valid
        provenance: lineage of the reconciliation
        confidence: confidence in the reconciliation (NOT a probability)
        notes: additional notes
        metadata: additional metadata
    """
    reconciliation_id: str
    effect_id: str
    observation_id: str
    reconstructed_path_id: str
    declared_graph_version: str
    declared_path_reference: str
    effective_path_reference: str
    correspondence_status: CorrespondenceStatus
    node_correspondence: bool
    edge_correspondence: bool
    provenance_correspondence: bool
    temporal_correspondence: TemporalReconciliationStatus
    scope_correspondence: ScopeReconciliationStatus
    domain_correspondence: DomainReconciliationStatus
    actor_correspondence: ActorReconciliationStatus
    capability_correspondence: bool
    governance_correspondence: bool
    trust_anchor_correspondence: bool
    delegation_correspondence: bool
    graph_completeness_status: GraphCompletenessStatus
    divergence_type: DivergenceType
    epistemic_status: EpistemicStatus
    historical_validity: bool
    current_validity: bool
    provenance: str
    confidence: float
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_reconciled(self) -> bool:
        return self.epistemic_status in (
            EpistemicStatus.RECONCILED,
            EpistemicStatus.RECONCILED_WITH_INCOMPLETE_DECLARED_GRAPH,
        )

    @property
    def is_escape(self) -> bool:
        return self.epistemic_status == EpistemicStatus.AUTHORITY_ESCAPE

    @property
    def is_divergent(self) -> bool:
        return self.epistemic_status == EpistemicStatus.DIVERGENT


# ---------------------------------------------------------------------------
# Reconciliation world — adversarial experimental substrate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReconciliationWorld:
    """An adversarial world for authority reconciliation experiments.

    Contains:
        declared_graph: the declared authority graph (oracle truth)
        observed_effect: the effect that was observed at runtime
        reconstructed_path: the path reconstructed from runtime evidence
        true_reconciliation: the true reconciliation relationship (oracle only)
        ground_truth_status: the expected correspondence status
        graph_completeness: whether the declared graph is complete
        graph_complete_for_scope: whether the graph is complete for this effect's scope
        has_alternate_paths: whether multiple valid declared paths exist
        is_emergency: whether this is an emergency authority path
        is_recovery: whether this is a recovery authority path
        is_background: whether this involves background execution
        is_cross_domain: whether this involves cross-domain authority
        is_replay: whether this involves a replayed authorization
        is_laundering: whether this involves authority laundering
        is_cyclic: whether the declared graph has cycles
        is_incomplete_graph: whether the declared graph is intentionally incomplete
        is_historical: whether the authority was historically valid but expired
        declared_path_executed: whether the declared path was actually exercised
    """
    world_id: str
    description: str
    observed_effect_id: str
    observed_effect_category: str
    observed_effect_source: str
    observed_effect_target: str
    observed_effect_scope: str
    observed_effect_domain: str
    observed_effect_actor: str
    observed_principal: str
    observed_capability: str
    declared_graph: DeclaredAuthorityGraph
    reconstructed_path: ReconstructedAuthorityPath
    true_reconciliation: CorrespondenceStatus
    ground_truth_epistemic: EpistemicStatus
    graph_completeness: GraphCompletenessStatus
    graph_complete_for_scope: bool
    has_alternate_paths: bool = False
    is_emergency: bool = False
    is_recovery: bool = False
    is_background: bool = False
    is_cross_domain: bool = False
    is_replay: bool = False
    is_laundering: bool = False
    is_cyclic: bool = False
    is_incomplete_graph: bool = False
    is_historical: bool = False
    declared_path_executed: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Oracle evaluation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OracleEvaluation:
    """Independent oracle evaluation of a reconciliation.

    The oracle knows the true reconciliation relationship but the
    reconciliation engine does not.
    """
    evaluation_id: str
    world_id: str
    reconstructed_status: CorrespondenceStatus
    true_status: CorrespondenceStatus
    status_match: bool
    epistemic_match: bool
    false_authorization: bool  # Reconciled as CORRESPONDS but actually ESCAPE/DIVERGENT
    false_escape: bool  # Reconciled as ESCAPE but actually CORRESPONDS
    false_divergence: bool  # Reconciled as DIVERGENT but actually CORRESPONDS
    missing_correspondence_correct: bool
    notes: str = ""


# ---------------------------------------------------------------------------
# Reconciliation engine
# ---------------------------------------------------------------------------


class ReconciliationEngine:
    """Reconciles reconstructed authority paths against the declared graph.

    CRITICAL INVARIANTS:
        RECONCILIATION ≠ AUTHORIZATION
        RECONSTRUCTED PATH ≠ DECLARED PATH
        DECLARED PATH ≠ EFFECTIVE PATH
        MISSING CORRESPONDENCE ≠ INVALID AUTHORITY
        GRAPH INCOMPLETENESS ≠ AUTHORITY ESCAPE
        RECONCILIATION MUST NOT CREATE AUTHORITY

    The engine determines the epistemic relationship between a reconstructed
    path and the declared graph. It does NOT authorize anything.
    """

    def __init__(self, engine_id: str):
        self.engine_id = engine_id
        self.reconciliations: list[AuthorityReconciliation] = []

    def reconcile(
        self,
        reconstructed_path: ReconstructedAuthorityPath,
        declared_graph: DeclaredAuthorityGraph,
        graph_completeness: GraphCompletenessStatus = GraphCompletenessStatus.UNKNOWN,
        graph_complete_for_scope: bool = True,
        has_alternate_paths: bool = False,
        is_emergency: bool = False,
        is_recovery: bool = False,
        is_background: bool = False,
        is_cross_domain: bool = False,
        is_replay: bool = False,
        is_laundering: bool = False,
        is_cyclic: bool = False,
        is_incomplete_graph: bool = False,
        is_historical: bool = False,
        declared_path_executed: bool = True,
    ) -> AuthorityReconciliation:
        """Reconcile a reconstructed path against the declared graph.

        This is the core method. It determines:
        1. Whether the reconstructed path corresponds to a declared path
        2. Whether the declared graph is complete enough to draw conclusions
        3. Whether the path diverges from the declared graph
        4. Whether the divergence is an authority escape or incomplete knowledge
        """
        # Step 1: Check reconstruction validity
        if reconstructed_path.validity == PathValidity.INVALID:
            return self._create_reconciliation(
                reconstructed_path=reconstructed_path,
                declared_graph=declared_graph,
                correspondence_status=CorrespondenceStatus.INVALID_RECONSTRUCTION,
                epistemic_status=EpistemicStatus.INVALID_RECONSTRUCTION,
                divergence_type=DivergenceType.NONE,
                graph_completeness=graph_completeness,
                notes="Reconstruction is invalid; cannot reconcile.",
            )

        if reconstructed_path.validity == PathValidity.UNKNOWN:
            return self._create_reconciliation(
                reconstructed_path=reconstructed_path,
                declared_graph=declared_graph,
                correspondence_status=CorrespondenceStatus.UNKNOWN,
                epistemic_status=EpistemicStatus.UNKNOWN,
                divergence_type=DivergenceType.UNKNOWN,
                graph_completeness=graph_completeness,
                notes="Reconstruction is unknown; cannot reconcile.",
            )

        # Step 2: Check for escape types in the reconstruction
        if reconstructed_path.escape_type != EscapeType.NO_ESCAPE:
            return self._handle_escape(
                reconstructed_path=reconstructed_path,
                declared_graph=declared_graph,
                graph_completeness=graph_completeness,
            )

        # Step 3: Check for cyclic declared graph
        if is_cyclic or not declared_graph.is_acyclic:
            return self._create_reconciliation(
                reconstructed_path=reconstructed_path,
                declared_graph=declared_graph,
                correspondence_status=CorrespondenceStatus.DIVERGES,
                epistemic_status=EpistemicStatus.DIVERGENT,
                divergence_type=DivergenceType.CYCLIC_DECLARED_GRAPH,
                graph_completeness=graph_completeness,
                notes="Declared graph contains cycles; path cannot be reconciled.",
            )

        # Step 4: Find matching declared path
        matching_path = self._find_matching_declared_path(
            reconstructed_path, declared_graph
        )

        # Step 5: Analyze correspondence
        if matching_path is not None:
            return self._analyze_correspondence(
                reconstructed_path=reconstructed_path,
                declared_graph=declared_graph,
                matching_path=matching_path,
                graph_completeness=graph_completeness,
                graph_complete_for_scope=graph_complete_for_scope,
                has_alternate_paths=has_alternate_paths,
                is_emergency=is_emergency,
                is_recovery=is_recovery,
                is_background=is_background,
                is_cross_domain=is_cross_domain,
                is_replay=is_replay,
                is_laundering=is_laundering,
                is_incomplete_graph=is_incomplete_graph,
                is_historical=is_historical,
                declared_path_executed=declared_path_executed,
            )

        # Step 6: No matching path found
        return self._handle_no_matching_path(
            reconstructed_path=reconstructed_path,
            declared_graph=declared_graph,
            graph_completeness=graph_completeness,
            graph_complete_for_scope=graph_complete_for_scope,
            is_incomplete_graph=is_incomplete_graph,
        )

    def _find_matching_declared_path(
        self,
        path: ReconstructedAuthorityPath,
        graph: DeclaredAuthorityGraph,
    ) -> list[str] | None:
        """Find a path in the declared graph that matches the reconstructed path.

        Matching is based on node types, principals, capabilities, scopes,
        and domains — NOT just identifiers.
        """
        # Start from trust anchor and try to find a matching chain
        if not path.nodes:
            return None

        # Find the trust anchor node in the graph
        anchor_nodes = [
            n for n in graph.nodes.values()
            if n.source_type == AuthoritySourceType.TRUST_ANCHOR
            and n.principal == path.nodes[0].principal
            and (n.scope == path.nodes[0].scope or n.scope == "*")
        ]

        if not anchor_nodes:
            return None

        # Try to find a path through the graph matching the reconstructed path
        for anchor in anchor_nodes:
            graph_path = self._trace_matching_path(path, graph, anchor.node_id)
            if graph_path is not None:
                return graph_path

        return None

    def _trace_matching_path(
        self,
        path: ReconstructedAuthorityPath,
        graph: DeclaredAuthorityGraph,
        start_node_id: str,
    ) -> list[str] | None:
        """Trace a path through the declared graph matching the reconstructed path."""
        graph_node_id = start_node_id
        matched_path: list[str] = [graph_node_id]

        # Skip the first node (trust anchor) since we already matched it
        for i, path_node in enumerate(path.nodes[1:], start=1):
            # Find an outgoing edge from current graph node that matches
            outgoing = graph.get_outgoing_edges(graph_node_id)
            found_match = False

            for edge in outgoing:
                target = graph.get_node(edge.target_node_id)
                if target is None:
                    continue

                # Match on node type, principal, and scope (most permissive)
                if (target.node_type == path_node.node_type and
                    target.principal == path_node.principal and
                    (target.scope == path_node.scope or target.scope == "*")):
                    matched_path.append(edge.target_node_id)
                    graph_node_id = edge.target_node_id
                    found_match = True
                    break

            if not found_match:
                return None

        return matched_path

    def _analyze_correspondence(
        self,
        reconstructed_path: ReconstructedAuthorityPath,
        declared_graph: DeclaredAuthorityGraph,
        matching_path: list[str],
        graph_completeness: GraphCompletenessStatus,
        graph_complete_for_scope: bool,
        has_alternate_paths: bool,
        is_emergency: bool,
        is_recovery: bool,
        is_background: bool,
        is_cross_domain: bool,
        is_replay: bool,
        is_laundering: bool,
        is_incomplete_graph: bool,
        is_historical: bool,
        declared_path_executed: bool,
    ) -> AuthorityReconciliation:
        """Analyze the correspondence between reconstructed and declared paths."""
        # Check provenance correspondence
        provenance_match = self._check_provenance_correspondence(
            reconstructed_path, declared_graph, matching_path
        )

        # Check temporal correspondence
        temporal_status = self._check_temporal_correspondence(
            reconstructed_path, declared_graph, matching_path, is_historical
        )

        # Check scope correspondence
        scope_status = self._check_scope_correspondence(
            reconstructed_path, declared_graph, matching_path
        )

        # Check domain correspondence
        domain_status = self._check_domain_correspondence(
            reconstructed_path, declared_graph, matching_path, is_cross_domain
        )

        # Check actor correspondence
        actor_status = self._check_actor_correspondence(
            reconstructed_path, is_background, is_emergency, is_recovery
        )

        # Check capability derivation correspondence
        capability_match = self._check_capability_correspondence(
            reconstructed_path, is_laundering
        )

        # Check governance correspondence
        governance_match = self._check_governance_correspondence(
            reconstructed_path, is_laundering
        )

        # Check trust anchor correspondence
        trust_anchor_match = self._check_trust_anchor_correspondence(
            reconstructed_path, declared_graph
        )

        # Check delegation correspondence
        delegation_match = self._check_delegation_correspondence(
            reconstructed_path, declared_graph, matching_path
        )

        # Determine divergence type
        divergence_type = self._determine_divergence_type(
            provenance_match=provenance_match,
            temporal_status=temporal_status,
            scope_status=scope_status,
            domain_status=domain_status,
            actor_status=actor_status,
            capability_match=capability_match,
            governance_match=governance_match,
            trust_anchor_match=trust_anchor_match,
            delegation_match=delegation_match,
            is_replay=is_replay,
            is_laundering=is_laundering,
            declared_path_executed=declared_path_executed,
        )

        # Determine overall correspondence status
        correspondence_status = self._determine_correspondence_status(
            divergence_type=divergence_type,
            graph_completeness=graph_completeness,
            graph_complete_for_scope=graph_complete_for_scope,
            has_alternate_paths=has_alternate_paths,
            declared_path_executed=declared_path_executed,
            is_emergency=is_emergency,
            is_recovery=is_recovery,
        )

        # Determine epistemic status
        epistemic_status = self._determine_epistemic_status(
            correspondence_status=correspondence_status,
            divergence_type=divergence_type,
        )

        return self._create_reconciliation(
            reconstructed_path=reconstructed_path,
            declared_graph=declared_graph,
            correspondence_status=correspondence_status,
            epistemic_status=epistemic_status,
            divergence_type=divergence_type,
            graph_completeness=graph_completeness,
            node_correspondence=True,
            edge_correspondence=True,
            provenance_correspondence=provenance_match,
            temporal_correspondence=temporal_status,
            scope_correspondence=scope_status,
            domain_correspondence=domain_status,
            actor_correspondence=actor_status,
            capability_correspondence=capability_match,
            governance_correspondence=governance_match,
            trust_anchor_correspondence=trust_anchor_match,
            delegation_correspondence=delegation_match,
            historical_validity=is_historical,
            current_validity=temporal_status == TemporalReconciliationStatus.VALID_AT_EXECUTION_AND_CURRENT,
            notes=self._generate_notes(
                divergence_type, correspondence_status, graph_completeness
            ),
        )

    def _handle_escape(
        self,
        reconstructed_path: ReconstructedAuthorityPath,
        declared_graph: DeclaredAuthorityGraph,
        graph_completeness: GraphCompletenessStatus,
    ) -> AuthorityReconciliation:
        """Handle cases where the reconstruction detected an escape."""
        escape_type = reconstructed_path.escape_type

        # Map escape types to divergence types
        divergence_map = {
            EscapeType.DIRECT_PRIMITIVE_BYPASS: DivergenceType.NODE_MISMATCH,
            EscapeType.AUTHORIZATION_LAUNDERING: DivergenceType.LAUNDERED_AUTHORIZATION,
            EscapeType.CAPABILITY_LAUNDERING: DivergenceType.LAUNDERED_CAPABILITY,
            EscapeType.GOVERNANCE_LAUNDERING: DivergenceType.LAUNDERED_GOVERNANCE,
            EscapeType.REPLAYED_RECEIPT: DivergenceType.REPLAYED_AUTHORIZATION,
            EscapeType.CYCLIC_DELEGATION: DivergenceType.CYCLIC_DECLARED_GRAPH,
            EscapeType.TEMPORAL_EXPIRED: DivergenceType.TEMPORAL_MISMATCH,
            EscapeType.CROSS_DOMAIN_MISMATCH: DivergenceType.DOMAIN_MISMATCH,
            EscapeType.UNDECLARED_DELEGATION: DivergenceType.DELEGATION_MISMATCH,
            EscapeType.UNRECOGNIZED_ANCHOR: DivergenceType.TRUST_ANCHOR_MISMATCH,
        }

        divergence_type = divergence_map.get(escape_type, DivergenceType.UNKNOWN)

        return self._create_reconciliation(
            reconstructed_path=reconstructed_path,
            declared_graph=declared_graph,
            correspondence_status=CorrespondenceStatus.AUTHORITY_ESCAPE,
            epistemic_status=EpistemicStatus.AUTHORITY_ESCAPE,
            divergence_type=divergence_type,
            graph_completeness=graph_completeness,
            notes=f"Authority escape detected: {escape_type.value}",
        )

    def _handle_no_matching_path(
        self,
        reconstructed_path: ReconstructedAuthorityPath,
        declared_graph: DeclaredAuthorityGraph,
        graph_completeness: GraphCompletenessStatus,
        graph_complete_for_scope: bool,
        is_incomplete_graph: bool,
    ) -> AuthorityReconciliation:
        """Handle cases where no matching declared path is found."""
        # If the graph is incomplete, missing correspondence ≠ escape
        if is_incomplete_graph or graph_completeness == GraphCompletenessStatus.INCOMPLETE:
            return self._create_reconciliation(
                reconstructed_path=reconstructed_path,
                declared_graph=declared_graph,
                correspondence_status=CorrespondenceStatus.NO_DECLARED_CORRESPONDENCE_FOUND,
                epistemic_status=EpistemicStatus.INCOMPLETE,
                divergence_type=DivergenceType.INCOMPLETE_GRAPH_EXPLAINS_DIVERGENCE,
                graph_completeness=graph_completeness,
                notes="No matching declared path, but graph is incomplete. Cannot conclude escape.",
            )

        # If the graph is complete for this scope, no correspondence = escape
        if graph_complete_for_scope:
            return self._create_reconciliation(
                reconstructed_path=reconstructed_path,
                declared_graph=declared_graph,
                correspondence_status=CorrespondenceStatus.AUTHORITY_ESCAPE,
                epistemic_status=EpistemicStatus.AUTHORITY_ESCAPE,
                divergence_type=DivergenceType.NO_DECLARED_CORRESPONDENCE,
                graph_completeness=graph_completeness,
                notes="No matching declared path and graph is complete for scope. Authority escape.",
            )

        # Unknown completeness
        return self._create_reconciliation(
            reconstructed_path=reconstructed_path,
            declared_graph=declared_graph,
            correspondence_status=CorrespondenceStatus.NO_DECLARED_CORRESPONDENCE_FOUND,
            epistemic_status=EpistemicStatus.UNKNOWN,
            divergence_type=DivergenceType.UNKNOWN,
            graph_completeness=graph_completeness,
            notes="No matching declared path. Graph completeness unknown.",
        )

    def _check_provenance_correspondence(
        self,
        path: ReconstructedAuthorityPath,
        graph: DeclaredAuthorityGraph,
        matching_path: list[str],
    ) -> bool:
        """Check whether provenance matches between reconstructed and declared paths."""
        # If both have no provenance, they match (both are unspecified)
        if not path.provenance:
            return True
        # Check if any node in the matching path has matching provenance
        for node_id in matching_path:
            node = graph.get_node(node_id)
            if node and node.provenance and node.provenance == path.provenance:
                return True
        return bool(path.provenance)

    def _check_temporal_correspondence(
        self,
        path: ReconstructedAuthorityPath,
        graph: DeclaredAuthorityGraph,
        matching_path: list[str],
        is_historical: bool,
    ) -> TemporalReconciliationStatus:
        """Check temporal correspondence."""
        if is_historical:
            return TemporalReconciliationStatus.HISTORICALLY_VALID

        if path.temporal_status == TemporalStatus.EXPIRED:
            return TemporalReconciliationStatus.EXPIRED_BEFORE_EXECUTION

        if path.temporal_status == TemporalStatus.NOT_YET_VALID:
            return TemporalReconciliationStatus.NOT_YET_VALID

        if path.temporal_status == TemporalStatus.HISTORICALLY_VALID:
            return TemporalReconciliationStatus.HISTORICALLY_VALID

        if path.temporal_status == TemporalStatus.CURRENTLY_VALID:
            return TemporalReconciliationStatus.VALID_AT_EXECUTION_AND_CURRENT

        return TemporalReconciliationStatus.VALID_AT_EXECUTION_AND_CURRENT

    def _check_scope_correspondence(
        self,
        path: ReconstructedAuthorityPath,
        graph: DeclaredAuthorityGraph,
        matching_path: list[str],
    ) -> ScopeReconciliationStatus:
        """Check scope correspondence."""
        if path.scope_status == ScopeStatus.MISMATCH:
            return ScopeReconciliationStatus.EFFECT_BROADER

        if path.scope_status == ScopeStatus.WIDENED:
            return ScopeReconciliationStatus.EFFECT_BROADER

        if path.scope_status == ScopeStatus.CROSS_DOMAIN_BLOCKED:
            return ScopeReconciliationStatus.SCOPE_MISMATCH

        # Check if declared scope matches
        for node_id in matching_path:
            node = graph.get_node(node_id)
            if node and node.scope != path.nodes[0].scope and node.scope != "*":
                return ScopeReconciliationStatus.SCOPE_MISMATCH

        return ScopeReconciliationStatus.MATCHING

    def _check_domain_correspondence(
        self,
        path: ReconstructedAuthorityPath,
        graph: DeclaredAuthorityGraph,
        matching_path: list[str],
        is_cross_domain: bool,
    ) -> DomainReconciliationStatus:
        """Check domain correspondence."""
        if is_cross_domain:
            # Cross-domain requires explicit delegation
            return DomainReconciliationStatus.CROSS_DOMAIN_BLOCKED

        if path.scope_status == ScopeStatus.CROSS_DOMAIN_BLOCKED:
            return DomainReconciliationStatus.CROSS_DOMAIN_BLOCKED

        return DomainReconciliationStatus.MATCHING

    def _check_actor_correspondence(
        self,
        path: ReconstructedAuthorityPath,
        is_background: bool,
        is_emergency: bool,
        is_recovery: bool,
    ) -> ActorReconciliationStatus:
        """Check actor correspondence."""
        if is_background:
            return ActorReconciliationStatus.CALLER_TO_WORKER_UNCONFIRMED

        if is_emergency:
            return ActorReconciliationStatus.EMERGENCY_ACTOR_VALID

        if is_recovery:
            return ActorReconciliationStatus.RECOVERY_ACTOR_VALID

        if path.attribution_status == AttributionStatus.CALLER_TO_WORKER_UNCONFIRMED:
            return ActorReconciliationStatus.CALLER_TO_WORKER_UNCONFIRMED

        if path.attribution_status == AttributionStatus.CONFIRMED:
            return ActorReconciliationStatus.MATCHING

        return ActorReconciliationStatus.MATCHING

    def _check_capability_correspondence(
        self,
        path: ReconstructedAuthorityPath,
        is_laundering: bool,
    ) -> bool:
        """Check capability derivation correspondence."""
        if is_laundering:
            return False

        if path.capability_status == CapabilityStatus.LAUNDERED:
            return False

        if path.capability_status == CapabilityStatus.VALID:
            return True

        return path.capability_status != CapabilityStatus.INVALID

    def _check_governance_correspondence(
        self,
        path: ReconstructedAuthorityPath,
        is_laundering: bool,
    ) -> bool:
        """Check governance correspondence."""
        if is_laundering:
            return False

        if path.governance_status == GovernanceStatus.LAUNDERED:
            return False

        if path.governance_status == GovernanceStatus.DISPOSITION_WITHOUT_AUTHORITY:
            return False

        if path.governance_status == GovernanceStatus.VALID:
            return True

        return path.governance_status != GovernanceStatus.INVALID

    def _check_trust_anchor_correspondence(
        self,
        path: ReconstructedAuthorityPath,
        graph: DeclaredAuthorityGraph,
    ) -> bool:
        """Check trust anchor correspondence."""
        if not path.trust_anchor_id:
            return False

        # Check if the trust anchor exists in the declared graph
        return path.trust_anchor_id in graph.trust_anchor_ids

    def _check_delegation_correspondence(
        self,
        path: ReconstructedAuthorityPath,
        graph: DeclaredAuthorityGraph,
        matching_path: list[str],
    ) -> bool:
        """Check delegation chain correspondence."""
        if not path.delegation_chain:
            return True  # No delegation to check

        # Check if delegation links exist in the declared graph
        for node_id in matching_path:
            node = graph.get_node(node_id)
            if node and node.source_type == AuthoritySourceType.DELEGATION:
                return True

        return len(path.delegation_chain) > 0

    def _determine_divergence_type(
        self,
        provenance_match: bool,
        temporal_status: TemporalReconciliationStatus,
        scope_status: ScopeReconciliationStatus,
        domain_status: DomainReconciliationStatus,
        actor_status: ActorReconciliationStatus,
        capability_match: bool,
        governance_match: bool,
        trust_anchor_match: bool,
        delegation_match: bool,
        is_replay: bool,
        is_laundering: bool,
        declared_path_executed: bool,
    ) -> DivergenceType:
        """Determine the type of divergence."""
        if not declared_path_executed:
            return DivergenceType.STATIC_POSSIBILITY_NOT_EXECUTED

        if is_replay:
            return DivergenceType.REPLAYED_AUTHORIZATION

        if is_laundering:
            return DivergenceType.LAUNDERED_AUTHORIZATION

        if not trust_anchor_match:
            return DivergenceType.TRUST_ANCHOR_MISMATCH

        if not delegation_match:
            return DivergenceType.DELEGATION_MISMATCH

        if not capability_match:
            return DivergenceType.CAPABILITY_DERIVATION_MISMATCH

        if not governance_match:
            return DivergenceType.GOVERNANCE_MISMATCH

        if temporal_status == TemporalReconciliationStatus.EXPIRED_BEFORE_EXECUTION:
            return DivergenceType.TEMPORAL_MISMATCH

        if temporal_status == TemporalReconciliationStatus.HISTORICALLY_VALID:
            return DivergenceType.HISTORICALLY_VALID_NOW_EXPIRED

        if scope_status == ScopeReconciliationStatus.EFFECT_BROADER:
            return DivergenceType.SCOPE_MISMATCH

        if scope_status == ScopeReconciliationStatus.SCOPE_MISMATCH:
            return DivergenceType.SCOPE_MISMATCH

        if domain_status == DomainReconciliationStatus.CROSS_DOMAIN_BLOCKED:
            return DivergenceType.DOMAIN_MISMATCH

        if domain_status == DomainReconciliationStatus.DOMAIN_MISMATCH:
            return DivergenceType.DOMAIN_MISMATCH

        if actor_status == ActorReconciliationStatus.ACTOR_MISMATCH:
            return DivergenceType.ACTOR_MISMATCH

        if actor_status == ActorReconciliationStatus.CALLER_TO_WORKER_UNCONFIRMED:
            return DivergenceType.ACTOR_MISMATCH

        if not provenance_match:
            return DivergenceType.PROVENANCE_MISMATCH

        return DivergenceType.NONE

    def _determine_correspondence_status(
        self,
        divergence_type: DivergenceType,
        graph_completeness: GraphCompletenessStatus,
        graph_complete_for_scope: bool,
        has_alternate_paths: bool,
        declared_path_executed: bool,
        is_emergency: bool,
        is_recovery: bool,
    ) -> CorrespondenceStatus:
        """Determine overall correspondence status."""
        if divergence_type == DivergenceType.NONE:
            if graph_completeness == GraphCompletenessStatus.INCOMPLETE:
                return CorrespondenceStatus.CORRESPONDS_WITH_INCOMPLETE_DECLARED_GRAPH
            return CorrespondenceStatus.CORRESPONDS

        if divergence_type == DivergenceType.STATIC_POSSIBILITY_NOT_EXECUTED:
            return CorrespondenceStatus.DIVERGES

        if divergence_type == DivergenceType.INCOMPLETE_GRAPH_EXPLAINS_DIVERGENCE:
            return CorrespondenceStatus.NO_DECLARED_CORRESPONDENCE_FOUND

        if divergence_type == DivergenceType.NO_DECLARED_CORRESPONDENCE:
            return CorrespondenceStatus.AUTHORITY_ESCAPE

        if divergence_type == DivergenceType.CYCLIC_DECLARED_GRAPH:
            return CorrespondenceStatus.DIVERGES

        if divergence_type == DivergenceType.REPLAYED_AUTHORIZATION:
            return CorrespondenceStatus.AUTHORITY_ESCAPE

        if divergence_type in (
            DivergenceType.LAUNDERED_AUTHORIZATION,
            DivergenceType.LAUNDERED_CAPABILITY,
            DivergenceType.LAUNDERED_GOVERNANCE,
        ):
            return CorrespondenceStatus.AUTHORITY_ESCAPE

        if divergence_type == DivergenceType.HISTORICALLY_VALID_NOW_EXPIRED:
            return CorrespondenceStatus.CORRESPONDS

        if divergence_type == DivergenceType.TEMPORAL_MISMATCH:
            return CorrespondenceStatus.DIVERGES

        if divergence_type == DivergenceType.SCOPE_MISMATCH:
            return CorrespondenceStatus.DIVERGES

        if divergence_type == DivergenceType.DOMAIN_MISMATCH:
            return CorrespondenceStatus.DIVERGES

        if divergence_type == DivergenceType.ACTOR_MISMATCH:
            if is_emergency or is_recovery:
                return CorrespondenceStatus.CORRESPONDS
            return CorrespondenceStatus.DIVERGES

        if divergence_type == DivergenceType.TRUST_ANCHOR_MISMATCH:
            return CorrespondenceStatus.AUTHORITY_ESCAPE

        if divergence_type == DivergenceType.DELEGATION_MISMATCH:
            return CorrespondenceStatus.DIVERGES

        if divergence_type == DivergenceType.CAPABILITY_DERIVATION_MISMATCH:
            return CorrespondenceStatus.AUTHORITY_ESCAPE

        if divergence_type == DivergenceType.GOVERNANCE_MISMATCH:
            return CorrespondenceStatus.AUTHORITY_ESCAPE

        if divergence_type == DivergenceType.PROVENANCE_MISMATCH:
            return CorrespondenceStatus.DIVERGES

        if divergence_type == DivergenceType.UNDECLARED_INTERMEDIATE:
            if graph_completeness == GraphCompletenessStatus.INCOMPLETE:
                return CorrespondenceStatus.CORRESPONDS_WITH_INCOMPLETE_DECLARED_GRAPH
            return CorrespondenceStatus.DIVERGES

        if divergence_type == DivergenceType.MULTIPLE_PATH_AMBIGUITY:
            return CorrespondenceStatus.DIVERGES

        return CorrespondenceStatus.UNKNOWN

    def _determine_epistemic_status(
        self,
        correspondence_status: CorrespondenceStatus,
        divergence_type: DivergenceType,
    ) -> EpistemicStatus:
        """Determine the epistemic status."""
        if correspondence_status == CorrespondenceStatus.CORRESPONDS:
            return EpistemicStatus.RECONCILED

        if correspondence_status == CorrespondenceStatus.CORRESPONDS_WITH_INCOMPLETE_DECLARED_GRAPH:
            return EpistemicStatus.RECONCILED_WITH_INCOMPLETE_DECLARED_GRAPH

        if correspondence_status == CorrespondenceStatus.AUTHORITY_ESCAPE:
            return EpistemicStatus.AUTHORITY_ESCAPE

        if correspondence_status == CorrespondenceStatus.DIVERGES:
            return EpistemicStatus.DIVERGENT

        if correspondence_status == CorrespondenceStatus.INCOMPLETE:
            return EpistemicStatus.INCOMPLETE

        if correspondence_status == CorrespondenceStatus.INVALID_RECONSTRUCTION:
            return EpistemicStatus.INVALID_RECONSTRUCTION

        if correspondence_status == CorrespondenceStatus.NO_DECLARED_CORRESPONDENCE_FOUND:
            if divergence_type == DivergenceType.INCOMPLETE_GRAPH_EXPLAINS_DIVERGENCE:
                return EpistemicStatus.INCOMPLETE
            return EpistemicStatus.AUTHORITY_ESCAPE

        return EpistemicStatus.UNKNOWN

    def _create_reconciliation(
        self,
        reconstructed_path: ReconstructedAuthorityPath,
        declared_graph: DeclaredAuthorityGraph,
        correspondence_status: CorrespondenceStatus,
        epistemic_status: EpistemicStatus,
        divergence_type: DivergenceType,
        graph_completeness: GraphCompletenessStatus,
        node_correspondence: bool = False,
        edge_correspondence: bool = False,
        provenance_correspondence: bool = False,
        temporal_correspondence: TemporalReconciliationStatus = TemporalReconciliationStatus.UNKNOWN,
        scope_correspondence: ScopeReconciliationStatus = ScopeReconciliationStatus.UNKNOWN,
        domain_correspondence: DomainReconciliationStatus = DomainReconciliationStatus.UNKNOWN,
        actor_correspondence: ActorReconciliationStatus = ActorReconciliationStatus.UNKNOWN,
        capability_correspondence: bool = False,
        governance_correspondence: bool = False,
        trust_anchor_correspondence: bool = False,
        delegation_correspondence: bool = False,
        historical_validity: bool = False,
        current_validity: bool = False,
        notes: str = "",
    ) -> AuthorityReconciliation:
        """Create a reconciliation record."""
        reconciliation = AuthorityReconciliation(
            reconciliation_id=f"recon-{uuid.uuid4().hex[:12]}",
            effect_id=reconstructed_path.effect_id,
            observation_id=reconstructed_path.observation_id,
            reconstructed_path_id=reconstructed_path.path_id,
            declared_graph_version=declared_graph.version,
            declared_path_reference="",
            effective_path_reference=reconstructed_path.path_id,
            correspondence_status=correspondence_status,
            node_correspondence=node_correspondence,
            edge_correspondence=edge_correspondence,
            provenance_correspondence=provenance_correspondence,
            temporal_correspondence=temporal_correspondence,
            scope_correspondence=scope_correspondence,
            domain_correspondence=domain_correspondence,
            actor_correspondence=actor_correspondence,
            capability_correspondence=capability_correspondence,
            governance_correspondence=governance_correspondence,
            trust_anchor_correspondence=trust_anchor_correspondence,
            delegation_correspondence=delegation_correspondence,
            graph_completeness_status=graph_completeness,
            divergence_type=divergence_type,
            epistemic_status=epistemic_status,
            historical_validity=historical_validity,
            current_validity=current_validity,
            provenance=f"{self.engine_id}:{reconstructed_path.path_id}",
            confidence=self._compute_confidence(correspondence_status, epistemic_status),
            notes=notes,
        )
        self.reconciliations.append(reconciliation)
        return reconciliation

    def _compute_confidence(
        self,
        correspondence_status: CorrespondenceStatus,
        epistemic_status: EpistemicStatus,
    ) -> float:
        """Compute confidence in the reconciliation.

        Confidence is NOT a probability of correctness.
        It is a measure of evidence sufficiency.
        """
        if epistemic_status == EpistemicStatus.RECONCILED:
            return 0.85
        elif epistemic_status == EpistemicStatus.RECONCILED_WITH_INCOMPLETE_DECLARED_GRAPH:
            return 0.65
        elif epistemic_status == EpistemicStatus.AUTHORITY_ESCAPE:
            return 0.75
        elif epistemic_status == EpistemicStatus.DIVERGENT:
            return 0.70
        elif epistemic_status == EpistemicStatus.INCOMPLETE:
            return 0.40
        elif epistemic_status == EpistemicStatus.INVALID_RECONSTRUCTION:
            return 0.30
        else:
            return 0.15

    def _generate_notes(
        self,
        divergence_type: DivergenceType,
        correspondence_status: CorrespondenceStatus,
        graph_completeness: GraphCompletenessStatus,
    ) -> str:
        """Generate human-readable notes."""
        parts = []
        if divergence_type != DivergenceType.NONE:
            parts.append(f"Divergence: {divergence_type.value}")
        parts.append(f"Correspondence: {correspondence_status.value}")
        parts.append(f"Graph completeness: {graph_completeness.value}")
        return "; ".join(parts)


# ---------------------------------------------------------------------------
# Independent oracle
# ---------------------------------------------------------------------------


class IndependentOracle:
    """Evaluates reconciliations against ground truth.

    The oracle knows the true reconciliation relationship but the
    reconciliation engine does not.
    """

    def evaluate(
        self,
        world: ReconciliationWorld,
        reconciliation: AuthorityReconciliation,
    ) -> OracleEvaluation:
        """Evaluate a reconciliation against ground truth."""
        status_match = (
            reconciliation.correspondence_status == world.true_reconciliation
        )
        epistemic_match = (
            reconciliation.epistemic_status == world.ground_truth_epistemic
        )

        # False authorization: reconciled as CORRESPONDS but actually ESCAPE/DIVERGENT
        false_authorization = (
            reconciliation.epistemic_status in (
                EpistemicStatus.RECONCILED,
                EpistemicStatus.RECONCILED_WITH_INCOMPLETE_DECLARED_GRAPH,
            )
            and world.ground_truth_epistemic in (
                EpistemicStatus.AUTHORITY_ESCAPE,
                EpistemicStatus.DIVERGENT,
            )
        )

        # False escape: reconciled as ESCAPE but actually CORRESPONDS
        false_escape = (
            reconciliation.epistemic_status == EpistemicStatus.AUTHORITY_ESCAPE
            and world.ground_truth_epistemic in (
                EpistemicStatus.RECONCILED,
                EpistemicStatus.RECONCILED_WITH_INCOMPLETE_DECLARED_GRAPH,
            )
        )

        # False divergence: reconciled as DIVERGENT but actually CORRESPONDS
        false_divergence = (
            reconciliation.epistemic_status == EpistemicStatus.DIVERGENT
            and world.ground_truth_epistemic in (
                EpistemicStatus.RECONCILED,
                EpistemicStatus.RECONCILED_WITH_INCOMPLETE_DECLARED_GRAPH,
            )
        )

        # Missing correspondence correctly identified
        missing_correspondence_correct = (
            reconciliation.correspondence_status
            == CorrespondenceStatus.NO_DECLARED_CORRESPONDENCE_FOUND
            and world.true_reconciliation
            == CorrespondenceStatus.NO_DECLARED_CORRESPONDENCE_FOUND
        )

        return OracleEvaluation(
            evaluation_id=f"eval-{uuid.uuid4().hex[:12]}",
            world_id=world.world_id,
            reconstructed_status=reconciliation.correspondence_status,
            true_status=world.true_reconciliation,
            status_match=status_match,
            epistemic_match=epistemic_match,
            false_authorization=false_authorization,
            false_escape=false_escape,
            false_divergence=false_divergence,
            missing_correspondence_correct=missing_correspondence_correct,
        )


# ---------------------------------------------------------------------------
# Adversarial world generator
# ---------------------------------------------------------------------------


class AdversarialWorldGenerator:
    """Generates adversarial worlds for Phase 32 experiments."""

    def generate_all_worlds(self) -> list[ReconciliationWorld]:
        """Generate all adversarial worlds."""
        worlds = [
            self._world_01_exact_correspondence(),
            self._world_02_valid_path_not_in_declared_graph(),
            self._world_03_declared_path_different_from_executed(),
            self._world_04_same_ids_different_provenance(),
            self._world_05_historically_valid_expired_at_execution(),
            self._world_06_valid_at_execution_expired_now(),
            self._world_07_wrong_scope(),
            self._world_08_wrong_actor(),
            self._world_09_wrong_domain(),
            self._world_10_valid_capability_wrong_ancestry(),
            self._world_11_valid_auth_id_forged_provenance(),
            self._world_12_valid_capability_id_forged_derivation(),
            self._world_13_governance_disposition_no_authority(),
            self._world_14_missing_trust_anchor(),
            self._world_15_missing_delegation(),
            self._world_16_missing_policy_authority(),
            self._world_17_missing_governance(),
            self._world_18_intentionally_incomplete_graph(),
            self._world_19_complete_for_scope_incomplete_globally(),
            self._world_20_multiple_valid_paths_one_used(),
            self._world_21_emergency_path_declared(),
            self._world_22_emergency_path_valid_but_omitted(),
            self._world_23_recovery_path_declared(),
            self._world_24_background_worker_no_delegation(),
            self._world_25_background_worker_with_delegation(),
            self._world_26_cross_domain_delegated(),
            self._world_27_cross_domain_observation_no_authority(),
            self._world_28_cyclic_declared_graph(),
            self._world_29_replayed_historical_authorization(),
            self._world_30_direct_primitive_escape(),
            self._world_31_no_available_provenance(),
            self._world_32_partial_provenance(),
            self._world_33_capability_mismatch(),
            self._world_34_undeclared_intermediate(),
            self._world_35_structurally_possible_never_exercised(),
        ]
        return worlds

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
            provenance=provenance or f"recon:{node_type}",
        )

    def _make_declared_node(
        self,
        node_id: str,
        node_type: str,
        principal: str,
        capability: str,
        scope: str = "runtime",
        domain: str = "default",
        source_type: AuthoritySourceType = AuthoritySourceType.DELEGATION,
        trust_anchor_id: str = "",
        temporal_valid_from: str = "unbounded",
        temporal_valid_until: str = "unbounded",
        provenance: str = "",
    ) -> DeclaredAuthorityNode:
        return DeclaredAuthorityNode(
            node_id=node_id,
            node_type=node_type,
            principal=principal,
            capability=capability,
            scope=scope,
            domain=domain,
            source_type=source_type,
            trust_anchor_id=trust_anchor_id,
            temporal_valid_from=temporal_valid_from,
            temporal_valid_until=temporal_valid_until,
            provenance=provenance,
        )

    def _make_declared_edge(
        self,
        source_node_id: str,
        target_node_id: str,
        delegation_capability: str = "",
        delegation_scope: str = "",
    ) -> DeclaredAuthorityEdge:
        return DeclaredAuthorityEdge(
            edge_id=f"edge-{uuid.uuid4().hex[:8]}",
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            delegation_capability=delegation_capability,
            delegation_scope=delegation_scope,
        )

    def _make_reconstructed_path(
        self,
        observation_id: str,
        effect_id: str,
        validity: PathValidity = PathValidity.VALID,
        nodes: tuple[AuthorityPathNode, ...] = (),
        trust_anchor_id: str = "ta-001",
        delegation_chain: tuple[str, ...] = ("del-001",),
        capability_status: CapabilityStatus = CapabilityStatus.VALID,
        governance_status: GovernanceStatus = GovernanceStatus.VALID,
        temporal_status: TemporalStatus = TemporalStatus.VALID,
        scope_status: ScopeStatus = ScopeStatus.VALID,
        attribution_status: AttributionStatus = AttributionStatus.CONFIRMED,
        escape_type: EscapeType = EscapeType.NO_ESCAPE,
        completeness_status: str = "complete_within_declared_graph",
        provenance: str = "",
        confidence: float = 0.9,
    ) -> ReconstructedAuthorityPath:
        return ReconstructedAuthorityPath(
            path_id=f"path-{uuid.uuid4().hex[:8]}",
            observation_id=observation_id,
            effect_id=effect_id,
            validity=validity,
            nodes=nodes,
            trust_anchor_id=trust_anchor_id,
            delegation_chain=("del-001",),
            capability_status=capability_status,
            governance_status=governance_status,
            temporal_status=temporal_status,
            scope_status=scope_status,
            attribution_status=attribution_status,
            escape_type=escape_type,
            completeness_status=completeness_status,
            provenance=provenance,
            confidence=confidence,
        )

    # -----------------------------------------------------------------------
    # World 01: Exact declared/effective correspondence
    # -----------------------------------------------------------------------

    def _world_01_exact_correspondence(self) -> ReconciliationWorld:
        """World 01: Exact correspondence between declared and reconstructed."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-01",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
            provenance="test:trust_anchor",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
            provenance="test:delegation",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="pol-001",
            node_type="policy",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.POLICY,
            trust_anchor_id="ta-001",
            provenance="test:policy",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="gov-001",
            node_type="governance",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.POLICY,
            trust_anchor_id="ta-001",
            provenance="test:governance",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="cap-001",
            node_type="capability",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.POLICY,
            trust_anchor_id="ta-001",
            provenance="test:capability",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="exe-001",
            node_type="execution_gate",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.POLICY,
            trust_anchor_id="ta-001",
            provenance="test:execution_gate",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="eff-001",
            node_type="effect",
            principal="admin",
            capability="subprocess.run",
            scope="runtime",
            source_type=AuthoritySourceType.POLICY,
            trust_anchor_id="ta-001",
            provenance="test:effect",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))
        declared_graph.add_edge(self._make_declared_edge("del-001", "pol-001"))
        declared_graph.add_edge(self._make_declared_edge("pol-001", "gov-001"))
        declared_graph.add_edge(self._make_declared_edge("gov-001", "cap-001"))
        declared_graph.add_edge(self._make_declared_edge("cap-001", "exe-001"))
        declared_graph.add_edge(self._make_declared_edge("exe-001", "eff-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-01",
            effect_id="eff-01",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_01_exact_correspondence",
            description="Exact correspondence between declared and reconstructed paths",
            observed_effect_id="eff-01",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.CORRESPONDS,
            ground_truth_epistemic=EpistemicStatus.RECONCILED,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
        )

    # -----------------------------------------------------------------------
    # World 02: Valid effective path not explicitly in declared graph
    # -----------------------------------------------------------------------

    def _world_02_valid_path_not_in_declared_graph(self) -> ReconciliationWorld:
        """World 02: Valid reconstructed path not explicitly in declared graph."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-02",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        # Missing intermediate nodes — graph is incomplete
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-02",
            effect_id="eff-02",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_02_valid_path_not_in_declared_graph",
            description="Valid reconstructed path not explicitly represented in declared graph",
            observed_effect_id="eff-02",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.CORRESPONDS_WITH_INCOMPLETE_DECLARED_GRAPH,
            ground_truth_epistemic=EpistemicStatus.RECONCILED_WITH_INCOMPLETE_DECLARED_GRAPH,
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=False,
            is_incomplete_graph=True,
        )

    # -----------------------------------------------------------------------
    # World 03: Declared path exists but was not the path that executed
    # -----------------------------------------------------------------------

    def _world_03_declared_path_different_from_executed(self) -> ReconciliationWorld:
        """World 03: Declared path exists but a different path executed."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-03",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="pol-001",
            node_type="policy",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.POLICY,
            trust_anchor_id="ta-001",
        ))
        # Declared path: ta -> del -> pol -> gov-A -> cap -> exe
        declared_graph.add_node(self._make_declared_node(
            node_id="gov-A",
            node_type="governance",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.POLICY,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))
        declared_graph.add_edge(self._make_declared_edge("del-001", "pol-001"))
        declared_graph.add_edge(self._make_declared_edge("pol-001", "gov-A"))

        # Reconstructed path uses gov-B (different intermediate)
        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute",
                           provenance="recon:gov-B"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-03",
            effect_id="eff-03",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_03_declared_path_different_from_executed",
            description="Declared path exists but a different path executed",
            observed_effect_id="eff-03",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.DIVERGES,
            ground_truth_epistemic=EpistemicStatus.DIVERGENT,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            declared_path_executed=False,
        )

    # -----------------------------------------------------------------------
    # World 04: Same node IDs but different provenance
    # -----------------------------------------------------------------------

    def _world_04_same_ids_different_provenance(self) -> ReconciliationWorld:
        """World 04: Declared and reconstructed paths share node IDs but differ in provenance."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-04",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
            provenance="declared:installation_time",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
            provenance="declared:admin_grant_2026",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*",
                           provenance="recon:different_installation"),
            self._make_node("delegation", "admin", "subprocess.execute",
                           provenance="recon:different_delegation"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-04",
            effect_id="eff-04",
            nodes=nodes,
            trust_anchor_id="ta-001",
            provenance="recon:different_provenance_chain",
        )

        return ReconciliationWorld(
            world_id="world_04_same_ids_different_provenance",
            description="Same node IDs but different provenance",
            observed_effect_id="eff-04",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.DIVERGES,
            ground_truth_epistemic=EpistemicStatus.DIVERGENT,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
        )

    # -----------------------------------------------------------------------
    # World 05: Historically valid but expired at execution
    # -----------------------------------------------------------------------

    def _world_05_historically_valid_expired_at_execution(self) -> ReconciliationWorld:
        """World 05: Authority was historically valid but expired before execution."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-05",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
            temporal_valid_from="2026-01-01T00:00:00Z",
            temporal_valid_until="2026-06-30T23:59:59Z",  # Expired
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute",
                           temporal_status=TemporalStatus.EXPIRED),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-05",
            effect_id="eff-05",
            nodes=nodes,
            trust_anchor_id="ta-001",
            temporal_status=TemporalStatus.EXPIRED,
        )

        return ReconciliationWorld(
            world_id="world_05_historically_valid_expired_at_execution",
            description="Authority was historically valid but expired before execution",
            observed_effect_id="eff-05",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.DIVERGES,
            ground_truth_epistemic=EpistemicStatus.DIVERGENT,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            is_historical=True,
        )

    # -----------------------------------------------------------------------
    # World 06: Valid at execution but expired now
    # -----------------------------------------------------------------------

    def _world_06_valid_at_execution_expired_now(self) -> ReconciliationWorld:
        """World 06: Authority was valid at execution time but has since expired."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-06",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
            temporal_valid_from="2026-01-01T00:00:00Z",
            temporal_valid_until="2026-12-31T23:59:59Z",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute",
                           temporal_status=TemporalStatus.HISTORICALLY_VALID),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-06",
            effect_id="eff-06",
            nodes=nodes,
            trust_anchor_id="ta-001",
            temporal_status=TemporalStatus.HISTORICALLY_VALID,
        )

        return ReconciliationWorld(
            world_id="world_06_valid_at_execution_expired_now",
            description="Authority was valid at execution but has since expired",
            observed_effect_id="eff-06",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.CORRESPONDS,
            ground_truth_epistemic=EpistemicStatus.RECONCILED,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            is_historical=True,
        )

    # -----------------------------------------------------------------------
    # World 07: Wrong scope
    # -----------------------------------------------------------------------

    def _world_07_wrong_scope(self) -> ReconciliationWorld:
        """World 07: Declared path has wrong scope."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-07",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="staging",  # Declared for staging
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="staging",  # Declared for staging
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*", scope="production"),
            self._make_node("delegation", "admin", "subprocess.execute", scope="production"),
            self._make_node("policy", "admin", "subprocess.execute", scope="production"),
            self._make_node("governance", "admin", "subprocess.execute", scope="production"),
            self._make_node("capability", "admin", "subprocess.execute", scope="production"),
            self._make_node("execution_gate", "admin", "subprocess.execute", scope="production"),
            self._make_node("effect", "admin", "subprocess.run", scope="production"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-07",
            effect_id="eff-07",
            nodes=nodes,
            trust_anchor_id="ta-001",
            scope_status=ScopeStatus.MISMATCH,
        )

        return ReconciliationWorld(
            world_id="world_07_wrong_scope",
            description="Declared path has wrong scope (staging vs production)",
            observed_effect_id="eff-07",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="production",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.DIVERGES,
            ground_truth_epistemic=EpistemicStatus.DIVERGENT,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
        )

    # -----------------------------------------------------------------------
    # World 08: Wrong actor
    # -----------------------------------------------------------------------

    def _world_08_wrong_actor(self) -> ReconciliationWorld:
        """World 08: Declared path has wrong actor."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-08",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="other-actor",  # Different actor
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-08",
            effect_id="eff-08",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_08_wrong_actor",
            description="Declared path has wrong actor",
            observed_effect_id="eff-08",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.DIVERGES,
            ground_truth_epistemic=EpistemicStatus.DIVERGENT,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
        )

    # -----------------------------------------------------------------------
    # World 09: Wrong domain
    # -----------------------------------------------------------------------

    def _world_09_wrong_domain(self) -> ReconciliationWorld:
        """World 09: Declared path has wrong domain."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-09",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="domain-a",  # Declared for domain-a
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            domain="domain-a",  # Declared for domain-a
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*", domain="domain-b"),
            self._make_node("delegation", "admin", "subprocess.execute", domain="domain-b"),
            self._make_node("policy", "admin", "subprocess.execute", domain="domain-b"),
            self._make_node("governance", "admin", "subprocess.execute", domain="domain-b"),
            self._make_node("capability", "admin", "subprocess.execute", domain="domain-b"),
            self._make_node("execution_gate", "admin", "subprocess.execute", domain="domain-b"),
            self._make_node("effect", "admin", "subprocess.run", domain="domain-b"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-09",
            effect_id="eff-09",
            nodes=nodes,
            trust_anchor_id="ta-001",
            scope_status=ScopeStatus.CROSS_DOMAIN_BLOCKED,
        )

        return ReconciliationWorld(
            world_id="world_09_wrong_domain",
            description="Declared path has wrong domain (domain-a vs domain-b)",
            observed_effect_id="eff-09",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="domain-b",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.DIVERGES,
            ground_truth_epistemic=EpistemicStatus.DIVERGENT,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            is_cross_domain=True,
        )

    # -----------------------------------------------------------------------
    # World 10: Valid capability but wrong authority ancestry
    # -----------------------------------------------------------------------

    def _world_10_valid_capability_wrong_ancestry(self) -> ReconciliationWorld:
        """World 10: Valid capability but derived from wrong authority."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-10",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute",
                           provenance="recon:different_ancestry"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-10",
            effect_id="eff-10",
            nodes=nodes,
            trust_anchor_id="ta-001",
            capability_status=CapabilityStatus.VALID,
        )

        return ReconciliationWorld(
            world_id="world_10_valid_capability_wrong_ancestry",
            description="Valid capability but derived from wrong authority ancestry",
            observed_effect_id="eff-10",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.AUTHORITY_ESCAPE,
            ground_truth_epistemic=EpistemicStatus.AUTHORITY_ESCAPE,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            is_laundering=True,
        )

    # -----------------------------------------------------------------------
    # World 11: Valid authorization ID but forged provenance
    # -----------------------------------------------------------------------

    def _world_11_valid_auth_id_forged_provenance(self) -> ReconciliationWorld:
        """World 11: Valid authorization ID but forged provenance."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-11",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-11",
            effect_id="eff-11",
            nodes=nodes,
            trust_anchor_id="ta-001",
            escape_type=EscapeType.AUTHORIZATION_LAUNDERING,
        )

        return ReconciliationWorld(
            world_id="world_11_valid_auth_id_forged_provenance",
            description="Valid authorization ID but forged provenance",
            observed_effect_id="eff-11",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.AUTHORITY_ESCAPE,
            ground_truth_epistemic=EpistemicStatus.AUTHORITY_ESCAPE,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            is_laundering=True,
        )

    # -----------------------------------------------------------------------
    # World 12: Valid capability ID but forged derivation
    # -----------------------------------------------------------------------

    def _world_12_valid_capability_id_forged_derivation(self) -> ReconciliationWorld:
        """World 12: Valid capability ID but forged derivation."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-12",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-12",
            effect_id="eff-12",
            nodes=nodes,
            trust_anchor_id="ta-001",
            capability_status=CapabilityStatus.LAUNDERED,
            escape_type=EscapeType.CAPABILITY_LAUNDERING,
        )

        return ReconciliationWorld(
            world_id="world_12_valid_capability_id_forged_derivation",
            description="Valid capability ID but forged derivation",
            observed_effect_id="eff-12",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.AUTHORITY_ESCAPE,
            ground_truth_epistemic=EpistemicStatus.AUTHORITY_ESCAPE,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            is_laundering=True,
        )

    # -----------------------------------------------------------------------
    # World 13: Governance disposition matching but no authority path
    # -----------------------------------------------------------------------

    def _world_13_governance_disposition_no_authority(self) -> ReconciliationWorld:
        """World 13: Governance disposition matches but no authority path."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-13",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-13",
            effect_id="eff-13",
            nodes=nodes,
            trust_anchor_id="ta-001",
            governance_status=GovernanceStatus.DISPOSITION_WITHOUT_AUTHORITY,
            escape_type=EscapeType.GOVERNANCE_LAUNDERING,
        )

        return ReconciliationWorld(
            world_id="world_13_governance_disposition_no_authority",
            description="Governance disposition matches but no authority path",
            observed_effect_id="eff-13",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.AUTHORITY_ESCAPE,
            ground_truth_epistemic=EpistemicStatus.AUTHORITY_ESCAPE,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            is_laundering=True,
        )

    # -----------------------------------------------------------------------
    # World 14: Missing trust anchor
    # -----------------------------------------------------------------------

    def _world_14_missing_trust_anchor(self) -> ReconciliationWorld:
        """World 14: Reconstructed path missing upstream trust anchor."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-14",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))

        nodes = (
            # Missing trust anchor node
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-14",
            effect_id="eff-14",
            nodes=nodes,
            trust_anchor_id="",  # Missing
        )

        return ReconciliationWorld(
            world_id="world_14_missing_trust_anchor",
            description="Reconstructed path missing upstream trust anchor",
            observed_effect_id="eff-14",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.INVALID_RECONSTRUCTION,
            ground_truth_epistemic=EpistemicStatus.INVALID_RECONSTRUCTION,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
        )

    # -----------------------------------------------------------------------
    # World 15: Missing delegation evidence
    # -----------------------------------------------------------------------

    def _world_15_missing_delegation(self) -> ReconciliationWorld:
        """World 15: Reconstructed path missing delegation evidence."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-15",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            # Missing delegation node
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-15",
            effect_id="eff-15",
            nodes=nodes,
            trust_anchor_id="ta-001",
            delegation_chain=(),  # Missing
        )

        return ReconciliationWorld(
            world_id="world_15_missing_delegation",
            description="Reconstructed path missing delegation evidence",
            observed_effect_id="eff-15",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.INCOMPLETE,
            ground_truth_epistemic=EpistemicStatus.INCOMPLETE,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
        )

    # -----------------------------------------------------------------------
    # World 16: Missing policy authority
    # -----------------------------------------------------------------------

    def _world_16_missing_policy_authority(self) -> ReconciliationWorld:
        """World 16: Reconstructed path missing policy authority."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-16",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="pol-001",
            node_type="policy",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.POLICY,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))
        declared_graph.add_edge(self._make_declared_edge("del-001", "pol-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            # Missing policy node
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-16",
            effect_id="eff-16",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_16_missing_policy_authority",
            description="Reconstructed path missing policy authority",
            observed_effect_id="eff-16",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.INCOMPLETE,
            ground_truth_epistemic=EpistemicStatus.INCOMPLETE,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
        )

    # -----------------------------------------------------------------------
    # World 17: Missing governance evidence
    # -----------------------------------------------------------------------

    def _world_17_missing_governance(self) -> ReconciliationWorld:
        """World 17: Reconstructed path missing governance evidence."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-17",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="gov-001",
            node_type="governance",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.POLICY,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))
        declared_graph.add_edge(self._make_declared_edge("del-001", "gov-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            # Missing governance node
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-17",
            effect_id="eff-17",
            nodes=nodes,
            trust_anchor_id="ta-001",
            governance_status=GovernanceStatus.MISSING,
        )

        return ReconciliationWorld(
            world_id="world_17_missing_governance",
            description="Reconstructed path missing governance evidence",
            observed_effect_id="eff-17",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.INCOMPLETE,
            ground_truth_epistemic=EpistemicStatus.INCOMPLETE,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
        )

    # -----------------------------------------------------------------------
    # World 18: Intentionally incomplete declared graph
    # -----------------------------------------------------------------------

    def _world_18_intentionally_incomplete_graph(self) -> ReconciliationWorld:
        """World 18: Declared graph is intentionally incomplete."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-18",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        # Graph is missing most nodes — intentionally incomplete

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-18",
            effect_id="eff-18",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_18_intentionally_incomplete_graph",
            description="Declared graph is intentionally incomplete",
            observed_effect_id="eff-18",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.NO_DECLARED_CORRESPONDENCE_FOUND,
            ground_truth_epistemic=EpistemicStatus.INCOMPLETE,
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=False,
            is_incomplete_graph=True,
        )

    # -----------------------------------------------------------------------
    # World 19: Complete for one effect category but incomplete globally
    # -----------------------------------------------------------------------

    def _world_19_complete_for_scope_incomplete_globally(self) -> ReconciliationWorld:
        """World 19: Declared graph complete for one scope but incomplete globally."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-19",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))
        # Missing other categories (network, filesystem, etc.)

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-19",
            effect_id="eff-19",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_19_complete_for_scope_incomplete_globally",
            description="Declared graph complete for subprocess scope but incomplete globally",
            observed_effect_id="eff-19",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.CORRESPONDS_WITH_INCOMPLETE_DECLARED_GRAPH,
            ground_truth_epistemic=EpistemicStatus.RECONCILED_WITH_INCOMPLETE_DECLARED_GRAPH,
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=True,
            is_incomplete_graph=True,
        )

    # -----------------------------------------------------------------------
    # World 20: Multiple valid declared paths, only one actually used
    # -----------------------------------------------------------------------

    def _world_20_multiple_valid_paths_one_used(self) -> ReconciliationWorld:
        """World 20: Multiple valid declared paths exist, only one actually used."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-20",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        # Path A
        declared_graph.add_node(self._make_declared_node(
            node_id="del-A",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        # Path B
        declared_graph.add_node(self._make_declared_node(
            node_id="del-B",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-A"))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-B"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-20",
            effect_id="eff-20",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_20_multiple_valid_paths_one_used",
            description="Multiple valid declared paths exist, only one actually used",
            observed_effect_id="eff-20",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.CORRESPONDS,
            ground_truth_epistemic=EpistemicStatus.RECONCILED,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            has_alternate_paths=True,
        )

    # -----------------------------------------------------------------------
    # World 21: Emergency authority path correctly declared
    # -----------------------------------------------------------------------

    def _world_21_emergency_path_declared(self) -> ReconciliationWorld:
        """World 21: Emergency authority path correctly declared."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-21",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="emg-001",
            node_type="delegation",
            principal="emergency-process",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "emg-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "emergency-process", "subprocess.execute"),
            self._make_node("policy", "emergency-process", "subprocess.execute"),
            self._make_node("governance", "emergency-process", "subprocess.execute"),
            self._make_node("capability", "emergency-process", "subprocess.execute"),
            self._make_node("execution_gate", "emergency-process", "subprocess.execute"),
            self._make_node("effect", "emergency-process", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-21",
            effect_id="eff-21",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_21_emergency_path_declared",
            description="Emergency authority path correctly declared",
            observed_effect_id="eff-21",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="emergency-process",
            observed_principal="emergency-process",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.CORRESPONDS,
            ground_truth_epistemic=EpistemicStatus.RECONCILED,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            is_emergency=True,
        )

    # -----------------------------------------------------------------------
    # World 22: Emergency path valid but omitted from ordinary policy graph
    # -----------------------------------------------------------------------

    def _world_22_emergency_path_valid_but_omitted(self) -> ReconciliationWorld:
        """World 22: Emergency path valid but omitted from ordinary policy graph."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-22",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        # Ordinary policy graph — emergency path NOT included
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "emergency-process", "subprocess.execute"),
            self._make_node("policy", "emergency-process", "subprocess.execute"),
            self._make_node("governance", "emergency-process", "subprocess.execute"),
            self._make_node("capability", "emergency-process", "subprocess.execute"),
            self._make_node("execution_gate", "emergency-process", "subprocess.execute"),
            self._make_node("effect", "emergency-process", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-22",
            effect_id="eff-22",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_22_emergency_path_valid_but_omitted",
            description="Emergency path valid but omitted from ordinary policy graph",
            observed_effect_id="eff-22",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="emergency-process",
            observed_principal="emergency-process",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.CORRESPONDS_WITH_INCOMPLETE_DECLARED_GRAPH,
            ground_truth_epistemic=EpistemicStatus.RECONCILED_WITH_INCOMPLETE_DECLARED_GRAPH,
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=False,
            is_emergency=True,
            is_incomplete_graph=True,
        )

    # -----------------------------------------------------------------------
    # World 23: Recovery authority path correctly declared
    # -----------------------------------------------------------------------

    def _world_23_recovery_path_declared(self) -> ReconciliationWorld:
        """World 23: Recovery authority path correctly declared."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-23",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="rec-001",
            node_type="delegation",
            principal="recovery-process",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "rec-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "recovery-process", "subprocess.execute"),
            self._make_node("policy", "recovery-process", "subprocess.execute"),
            self._make_node("governance", "recovery-process", "subprocess.execute"),
            self._make_node("capability", "recovery-process", "subprocess.execute"),
            self._make_node("execution_gate", "recovery-process", "subprocess.execute"),
            self._make_node("effect", "recovery-process", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-23",
            effect_id="eff-23",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_23_recovery_path_declared",
            description="Recovery authority path correctly declared",
            observed_effect_id="eff-23",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="recovery-process",
            observed_principal="recovery-process",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.CORRESPONDS,
            ground_truth_epistemic=EpistemicStatus.RECONCILED,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            is_recovery=True,
        )

    # -----------------------------------------------------------------------
    # World 24: Background worker where caller authority must not transfer
    # -----------------------------------------------------------------------

    def _world_24_background_worker_no_delegation(self) -> ReconciliationWorld:
        """World 24: Background worker where caller authority must not transfer."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-24",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "worker-process", "subprocess.run"),  # Different actor
        )
        path = self._make_reconstructed_path(
            observation_id="obs-24",
            effect_id="eff-24",
            nodes=nodes,
            trust_anchor_id="ta-001",
            attribution_status=AttributionStatus.CALLER_TO_WORKER_UNCONFIRMED,
        )

        return ReconciliationWorld(
            world_id="world_24_background_worker_no_delegation",
            description="Background worker where caller authority must not transfer",
            observed_effect_id="eff-24",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="worker-process",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.DIVERGES,
            ground_truth_epistemic=EpistemicStatus.DIVERGENT,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            is_background=True,
        )

    # -----------------------------------------------------------------------
    # World 25: Background worker with explicit delegated authority
    # -----------------------------------------------------------------------

    def _world_25_background_worker_with_delegation(self) -> ReconciliationWorld:
        """World 25: Background worker with explicit delegated authority."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-25",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-002",
            node_type="delegation",
            principal="worker-process",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))
        declared_graph.add_edge(self._make_declared_edge("del-001", "del-002"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("delegation", "worker-process", "subprocess.execute"),
            self._make_node("policy", "worker-process", "subprocess.execute"),
            self._make_node("governance", "worker-process", "subprocess.execute"),
            self._make_node("capability", "worker-process", "subprocess.execute"),
            self._make_node("execution_gate", "worker-process", "subprocess.execute"),
            self._make_node("effect", "worker-process", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-25",
            effect_id="eff-25",
            nodes=nodes,
            trust_anchor_id="ta-001",
            attribution_status=AttributionStatus.CONFIRMED,
        )

        return ReconciliationWorld(
            world_id="world_25_background_worker_with_delegation",
            description="Background worker with explicit delegated authority",
            observed_effect_id="eff-25",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="worker-process",
            observed_principal="worker-process",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.CORRESPONDS,
            ground_truth_epistemic=EpistemicStatus.RECONCILED,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            is_background=True,
        )

    # -----------------------------------------------------------------------
    # World 26: Cross-domain delegated authority
    # -----------------------------------------------------------------------

    def _world_26_cross_domain_delegated(self) -> ReconciliationWorld:
        """World 26: Cross-domain delegated authority."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-26",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="domain-a",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            domain="domain-b",  # Cross-domain delegation
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*", domain="domain-a"),
            self._make_node("delegation", "admin", "subprocess.execute", domain="domain-b"),
            self._make_node("policy", "admin", "subprocess.execute", domain="domain-b"),
            self._make_node("governance", "admin", "subprocess.execute", domain="domain-b"),
            self._make_node("capability", "admin", "subprocess.execute", domain="domain-b"),
            self._make_node("execution_gate", "admin", "subprocess.execute", domain="domain-b"),
            self._make_node("effect", "admin", "subprocess.run", domain="domain-b"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-26",
            effect_id="eff-26",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_26_cross_domain_delegated",
            description="Cross-domain delegated authority",
            observed_effect_id="eff-26",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="domain-b",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.CORRESPONDS,
            ground_truth_epistemic=EpistemicStatus.RECONCILED,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            is_cross_domain=True,
        )

    # -----------------------------------------------------------------------
    # World 27: Cross-domain observation without cross-domain authority
    # -----------------------------------------------------------------------

    def _world_27_cross_domain_observation_no_authority(self) -> ReconciliationWorld:
        """World 27: Cross-domain observation without cross-domain authority."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-27",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="domain-a",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            domain="domain-a",  # Only domain-a
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*", domain="domain-a"),
            self._make_node("delegation", "admin", "subprocess.execute", domain="domain-b"),
            self._make_node("policy", "admin", "subprocess.execute", domain="domain-b"),
            self._make_node("governance", "admin", "subprocess.execute", domain="domain-b"),
            self._make_node("capability", "admin", "subprocess.execute", domain="domain-b"),
            self._make_node("execution_gate", "admin", "subprocess.execute", domain="domain-b"),
            self._make_node("effect", "admin", "subprocess.run", domain="domain-b"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-27",
            effect_id="eff-27",
            nodes=nodes,
            trust_anchor_id="ta-001",
            scope_status=ScopeStatus.CROSS_DOMAIN_BLOCKED,
        )

        return ReconciliationWorld(
            world_id="world_27_cross_domain_observation_no_authority",
            description="Cross-domain observation without cross-domain authority",
            observed_effect_id="eff-27",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="domain-b",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.AUTHORITY_ESCAPE,
            ground_truth_epistemic=EpistemicStatus.AUTHORITY_ESCAPE,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            is_cross_domain=True,
        )

    # -----------------------------------------------------------------------
    # World 28: Cyclic declared graph
    # -----------------------------------------------------------------------

    def _world_28_cyclic_declared_graph(self) -> ReconciliationWorld:
        """World 28: Cyclic declared graph."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-28",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="pol-001",
            node_type="policy",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.POLICY,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))
        declared_graph.add_edge(self._make_declared_edge("del-001", "pol-001"))
        declared_graph.add_edge(self._make_declared_edge("pol-001", "ta-001"))  # Cycle!

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-28",
            effect_id="eff-28",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_28_cyclic_declared_graph",
            description="Cyclic declared graph",
            observed_effect_id="eff-28",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.DIVERGES,
            ground_truth_epistemic=EpistemicStatus.DIVERGENT,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            is_cyclic=True,
        )

    # -----------------------------------------------------------------------
    # World 29: Replayed historical authorization
    # -----------------------------------------------------------------------

    def _world_29_replayed_historical_authorization(self) -> ReconciliationWorld:
        """World 29: Replayed historical authorization."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-29",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
            temporal_valid_from="2026-01-01T00:00:00Z",
            temporal_valid_until="2026-06-30T23:59:59Z",  # Expired
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-29",
            effect_id="eff-29",
            nodes=nodes,
            trust_anchor_id="ta-001",
            escape_type=EscapeType.REPLAYED_RECEIPT,
        )

        return ReconciliationWorld(
            world_id="world_29_replayed_historical_authorization",
            description="Replayed historical authorization",
            observed_effect_id="eff-29",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.AUTHORITY_ESCAPE,
            ground_truth_epistemic=EpistemicStatus.AUTHORITY_ESCAPE,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            is_replay=True,
            is_historical=True,
        )

    # -----------------------------------------------------------------------
    # World 30: Direct primitive effect with no authority path
    # -----------------------------------------------------------------------

    def _world_30_direct_primitive_escape(self) -> ReconciliationWorld:
        """World 30: Direct primitive effect with no authority path."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-30",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))

        nodes = (
            self._make_node("effect", "unknown", "subprocess.run"),  # No authority path
        )
        path = self._make_reconstructed_path(
            observation_id="obs-30",
            effect_id="eff-30",
            nodes=nodes,
            trust_anchor_id="",
            escape_type=EscapeType.DIRECT_PRIMITIVE_BYPASS,
        )

        return ReconciliationWorld(
            world_id="world_30_direct_primitive_escape",
            description="Direct primitive effect with no authority path",
            observed_effect_id="eff-30",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="unknown",
            observed_principal="unknown",
            observed_capability="subprocess.run",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.AUTHORITY_ESCAPE,
            ground_truth_epistemic=EpistemicStatus.AUTHORITY_ESCAPE,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
        )

    # -----------------------------------------------------------------------
    # World 31: Observed effect with no available provenance
    # -----------------------------------------------------------------------

    def _world_31_no_available_provenance(self) -> ReconciliationWorld:
        """World 31: Observed effect with no available provenance."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-31",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))

        nodes = (
            self._make_node("effect", "admin", "subprocess.run",
                           status=PathNodeStatus.UNVERIFIED),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-31",
            effect_id="eff-31",
            nodes=nodes,
            trust_anchor_id="",
            validity=PathValidity.UNKNOWN,
        )

        return ReconciliationWorld(
            world_id="world_31_no_available_provenance",
            description="Observed effect with no available provenance",
            observed_effect_id="eff-31",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.UNKNOWN,
            ground_truth_epistemic=EpistemicStatus.UNKNOWN,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
        )

    # -----------------------------------------------------------------------
    # World 32: Observed effect with partial provenance
    # -----------------------------------------------------------------------

    def _world_32_partial_provenance(self) -> ReconciliationWorld:
        """World 32: Observed effect with partial provenance."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-32",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            # Missing policy, governance, capability nodes
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-32",
            effect_id="eff-32",
            nodes=nodes,
            trust_anchor_id="ta-001",
            validity=PathValidity.INCOMPLETE,
        )

        return ReconciliationWorld(
            world_id="world_32_partial_provenance",
            description="Observed effect with partial provenance",
            observed_effect_id="eff-32",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.INCOMPLETE,
            ground_truth_epistemic=EpistemicStatus.INCOMPLETE,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
        )

    # -----------------------------------------------------------------------
    # World 33: Declared graph says capability exists, runtime says different
    # -----------------------------------------------------------------------

    def _world_33_capability_mismatch(self) -> ReconciliationWorld:
        """World 33: Declared graph says capability exists, runtime evidence says different capability executed."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-33",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="network.execute",  # Declared: network
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),  # Reconstructed: subprocess
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-33",
            effect_id="eff-33",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_33_capability_mismatch",
            description="Declared graph says capability exists, runtime says different capability executed",
            observed_effect_id="eff-33",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.DIVERGES,
            ground_truth_epistemic=EpistemicStatus.DIVERGENT,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
        )

    # -----------------------------------------------------------------------
    # World 34: Effective path contains an undeclared intermediate authority transition
    # -----------------------------------------------------------------------

    def _world_34_undeclared_intermediate(self) -> ReconciliationWorld:
        """World 34: Effective path contains an undeclared intermediate authority transition."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-34",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_node(self._make_declared_node(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-001"))
        # Missing intermediate nodes

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-34",
            effect_id="eff-34",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_34_undeclared_intermediate",
            description="Effective path contains an undeclared intermediate authority transition",
            observed_effect_id="eff-34",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.CORRESPONDS_WITH_INCOMPLETE_DECLARED_GRAPH,
            ground_truth_epistemic=EpistemicStatus.RECONCILED_WITH_INCOMPLETE_DECLARED_GRAPH,
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=False,
            is_incomplete_graph=True,
        )

    # -----------------------------------------------------------------------
    # World 35: Declared graph contains a path that is structurally possible but never actually exercised
    # -----------------------------------------------------------------------

    def _world_35_structurally_possible_never_exercised(self) -> ReconciliationWorld:
        """World 35: Declared graph contains a path that is structurally possible but never actually exercised."""
        declared_graph = DeclaredAuthorityGraph(
            graph_id="graph-35",
            version="v1",
        )
        declared_graph.add_node(self._make_declared_node(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        # Path A: declared but never executed
        declared_graph.add_node(self._make_declared_node(
            node_id="del-A",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        # Path B: actually executed
        declared_graph.add_node(self._make_declared_node(
            node_id="del-B",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-A"))
        declared_graph.add_edge(self._make_declared_edge("ta-001", "del-B"))

        nodes = (
            self._make_node("trust_anchor", "admin", "*"),
            self._make_node("delegation", "admin", "subprocess.execute"),
            self._make_node("policy", "admin", "subprocess.execute"),
            self._make_node("governance", "admin", "subprocess.execute"),
            self._make_node("capability", "admin", "subprocess.execute"),
            self._make_node("execution_gate", "admin", "subprocess.execute"),
            self._make_node("effect", "admin", "subprocess.run"),
        )
        path = self._make_reconstructed_path(
            observation_id="obs-35",
            effect_id="eff-35",
            nodes=nodes,
            trust_anchor_id="ta-001",
        )

        return ReconciliationWorld(
            world_id="world_35_structurally_possible_never_exercised",
            description="Declared graph contains a path that is structurally possible but never actually exercised",
            observed_effect_id="eff-35",
            observed_effect_category="subprocess",
            observed_effect_source="src/sas/argopack.py",
            observed_effect_target="subprocess.run",
            observed_effect_scope="runtime",
            observed_effect_domain="default",
            observed_effect_actor="admin",
            observed_principal="admin",
            observed_capability="subprocess.execute",
            declared_graph=declared_graph,
            reconstructed_path=path,
            true_reconciliation=CorrespondenceStatus.CORRESPONDS,
            ground_truth_epistemic=EpistemicStatus.RECONCILED,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            has_alternate_paths=True,
            declared_path_executed=False,
        )


# ---------------------------------------------------------------------------
# Phase 32 experiment
# ---------------------------------------------------------------------------


class Phase32Experiment:
    """Runs the complete Phase 32 experiment."""

    def __init__(self) -> None:
        self.engine = ReconciliationEngine("phase32-engine")
        self.oracle = IndependentOracle()
        self.worlds = AdversarialWorldGenerator().generate_all_worlds()
        self.results: list[dict[str, Any]] = []

    def run_all(self) -> dict[str, Any]:
        """Run all worlds and return summary."""
        for world in self.worlds:
            reconciliation = self.engine.reconcile(
                reconstructed_path=world.reconstructed_path,
                declared_graph=world.declared_graph,
                graph_completeness=world.graph_completeness,
                graph_complete_for_scope=world.graph_complete_for_scope,
                has_alternate_paths=world.has_alternate_paths,
                is_emergency=world.is_emergency,
                is_recovery=world.is_recovery,
                is_background=world.is_background,
                is_cross_domain=world.is_cross_domain,
                is_replay=world.is_replay,
                is_laundering=world.is_laundering,
                is_cyclic=world.is_cyclic,
                is_incomplete_graph=world.is_incomplete_graph,
                is_historical=world.is_historical,
                declared_path_executed=world.declared_path_executed,
            )
            evaluation = self.oracle.evaluate(world, reconciliation)
            self.results.append({
                "world_id": world.world_id,
                "correspondence_status": reconciliation.correspondence_status.value,
                "epistemic_status": reconciliation.epistemic_status.value,
                "divergence_type": reconciliation.divergence_type.value,
                "status_match": evaluation.status_match,
                "epistemic_match": evaluation.epistemic_match,
                "false_authorization": evaluation.false_authorization,
                "false_escape": evaluation.false_escape,
                "false_divergence": evaluation.false_divergence,
            })
        return self.summary()

    def summary(self) -> dict[str, Any]:
        """Generate experiment summary."""
        total = len(self.results)
        status_matches = sum(1 for r in self.results if r["status_match"])
        epistemic_matches = sum(1 for r in self.results if r["epistemic_match"])
        false_authorizations = sum(1 for r in self.results if r["false_authorization"])
        false_escapes = sum(1 for r in self.results if r["false_escape"])
        false_divergences = sum(1 for r in self.results if r["false_divergence"])

        return {
            "total_worlds": total,
            "total_reconciliations": len(self.engine.reconciliations),
            "status_matches": status_matches,
            "epistemic_matches": epistemic_matches,
            "false_authorizations": false_authorizations,
            "false_escapes": false_escapes,
            "false_divergences": false_divergences,
            "status_accuracy": status_matches / total if total > 0 else 0,
            "epistemic_accuracy": epistemic_matches / total if total > 0 else 0,
        }
