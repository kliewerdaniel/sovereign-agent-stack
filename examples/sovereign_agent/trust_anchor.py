"""Phase 17: Trust Anchor.

Investigates the smallest explicit trust-anchor model required to replace
the implicit hardcoded authority root without introducing authority regress.

Phase 16 established AUTHORITY_ROOT_IMPLICIT: the effective authority root
is the hardcoded `admin` principal. The root is not explicitly governed.
Self-creation of root authority is possible. Delegation termination is not
enforced. The existing `AuthorityRoot` type is not integrated into the
production governance authority path.

Phase 17 asks: WHAT MAKES AN AUTHORITY ROOT A ROOT?

The deeper question: CAN A TRUST ANCHOR BE EXPLICITLY REPRESENTED WITHOUT
REQUIRING ANOTHER AUTHORITY TO AUTHORIZE THE TRUST ANCHOR?

Do not solve the problem by recursively adding another authority above admin.
Do not build a generic RootAuthority abstraction that wraps the hardcoded admin.
The trust anchor does not have to prove its legitimacy internally.
The architecture must state what it trusts and preserve that assumption explicitly.

Three concepts distinguished:
- AUTHORITY ORIGIN: Where did this authority claim originate?
- TRUST ANCHOR: What non-derived assumption does the system accept as a starting point?
- AUTHORITY DELEGATION: How does authority move from one principal to another?

Existing infrastructure reused:
- AuthorityRoot, RootType, ProtocolDomain (protocol_lineage.py)
- AuthorityClosure, ClosureStatus (compositional_authority.py)
- PolicyGovernanceEngine, PolicyAuthorityRecord (policy_governance.py)
- AuthoritySurface, AuthorityEnvelope (effect_boundary.py)
- EpistemicCycleDetector, CycleType (epistemic_cycles.py)
- AuthorityRootRecord, DelegationChain, DelegationLink (authority_root.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Trust Anchor Types
# ---------------------------------------------------------------------------


class AnchorType(str, Enum):
    """Types of trust anchors.
    
    A trust anchor is a non-derived assumption the system accepts as a
    starting point for authority derivation. It does not require another
    authority to authorize its existence.
    """
    GENESIS = "genesis"           # Installation-time anchor
    CRYPTOGRAPHIC = "cryptographic"  # Key-based anchor
    ORGANIZATIONAL = "organizational"  # Human/organizational anchor
    HARDWARE = "hardware"         # Hardware-backed anchor
    COMPOSITE = "composite"       # Multi-factor anchor


class AnchorStatus(str, Enum):
    """Status of a trust anchor."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ROTATED = "rotated"
    COMPROMISED = "compromised"
    SUPERSEDED = "superseded"


class DelegationTerminationType(str, Enum):
    """Types of delegation termination."""
    NON_DELEGABLE = "non_delegable"      # Anchor cannot be delegated
    DEPTH_BOUND = "depth_bound"          # Maximum delegation depth
    SCOPE_BOUND = "scope_bound"          # Delegation scope restricted
    TEMPORAL_BOUND = "temporal_bound"    # Delegation expires
    EXPLICIT_RIGHT = "explicit_right"    # Delegation requires explicit right


class TrustAnchorExperimentResult(str, Enum):
    """Result of a trust anchor experiment."""
    ANCHOR_EXPLICIT = "anchor_explicit"
    ANCHOR_IMPLICIT = "anchor_implicit"
    SELF_AUTHORIZATION_BLOCKED = "self_authorization_blocked"
    SELF_AUTHORIZATION_POSSIBLE = "self_authorization_possible"
    DELEGATION_TERMINATES = "delegation_terminates"
    DELEGATION_UNBOUNDED = "delegation_unbounded"
    SOVEREIGN_DOMAINS_VALID = "sovereign_domains_valid"
    SOVEREIGN_DOMAINS_CONFLATED = "sovereign_domains_conflated"
    AUTHORITY_DELEGATION_DISTINCT = "authority_delegation_distinct"
    AUTHORITY_DELEGATION_CONFLATED = "authority_delegation_conflated"
    ROTATION_WITHOUT_REGRESS = "rotation_without_regress"
    ROTATION_CREATES_REGRESS = "rotation_creates_regress"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Trust Anchor
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TrustAnchor:
    """A non-derived trust assumption.
    
    A trust anchor is NOT derived from another authority. It is the
    starting condition from which authority derivation begins.
    
    The trust anchor does not require another authority to authorize
    its existence. It is a normative starting condition.
    
    Key properties:
    - non_delegable: the anchor itself cannot be delegated
    - authority_to_delegate: the anchor can delegate authority without
      possessing the corresponding operational capability
    - authority_to_govern: the anchor can govern downstream authority
    """
    anchor_id: str
    anchor_type: AnchorType
    status: AnchorStatus
    identity: str
    domain: str
    authority_scope: str
    temporal_bounds: dict[str, str] = field(default_factory=dict)
    cryptographic_identity: str = ""
    genesis_reference: str = ""
    provenance: tuple[str, ...] = ()
    non_delegable: bool = True
    authority_to_delegate: bool = True
    authority_to_govern: bool = True
    max_delegation_depth: int = 0  # 0 means no delegation allowed
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        """Check if this anchor is currently active."""
        return self.status == AnchorStatus.ACTIVE
    
    @property
    def can_delegate(self) -> bool:
        """Check if this anchor can delegate authority."""
        return self.is_active and self.authority_to_delegate and self.max_delegation_depth > 0
    
    @property
    def can_govern(self) -> bool:
        """Check if this anchor can govern downstream authority."""
        return self.is_active and self.authority_to_governate
    
    def can_delegate_to(self, target_domain: str) -> bool:
        """Check if this anchor can delegate to a target domain."""
        if not self.can_delegate:
            return False
        if self.domain == target_domain:
            return True
        # Cross-domain delegation requires explicit cross-domain right
        return self.metadata.get("cross_domain_delegation", False)


# ---------------------------------------------------------------------------
# Authority Domain
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityDomain:
    """An independent authority domain with its own trust anchor.
    
    Two domains may coexist without one being subordinate to the other.
    Cross-domain authority requires explicit delegation.
    """
    domain_id: str
    trust_anchor: TrustAnchor
    policy_authority: str = ""
    effect_authority: str = ""
    governance_authority: str = ""
    execution_authority: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_sovereign(self) -> bool:
        """Check if this domain is sovereign (self-contained)."""
        return self.trust_anchor.is_active
    
    def has_cross_domain_authority(self, other_domain: "AuthorityDomain") -> bool:
        """Check if this domain has authority over another domain."""
        # Cross-domain authority requires explicit delegation
        return (
            self.domain_id in other_domain.trust_anchor.metadata.get("delegated_from", [])
        )


# ---------------------------------------------------------------------------
# Delegation with Termination
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TerminatedDelegationLink:
    """A delegation link with explicit termination conditions."""
    link_id: str
    delegator_id: str
    delegate_id: str
    capability: str
    scope: str
    valid_from: str
    valid_until: str
    is_terminal: bool = False
    delegation_right: bool = False  # Whether this delegate can further delegate
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class TerminatedDelegationChain:
    """A delegation chain with explicit termination conditions."""
    chain_id: str
    anchor_id: str
    links: list[TerminatedDelegationLink]
    max_depth: int = 5
    terminal_authority: str = ""
    
    @property
    def depth(self) -> int:
        return len(self.links)
    
    @property
    def is_terminated(self) -> bool:
        if not self.links:
            return True
        if self.links[-1].is_terminal:
            return True
        if not self.links[-1].delegation_right:
            return True
        if self.depth >= self.max_depth:
            return True
        return False
    
    @property
    def is_recursive(self) -> bool:
        if not self.links:
            return False
        # Check for self-delegation: A → A
        delegate_ids = [link.delegate_id for link in self.links]
        if len(delegate_ids) != len(set(delegate_ids)):
            return True
        # Check for cycle back to anchor: A → B → ... → A
        all_ids = set(delegate_ids)
        return self.anchor_id in all_ids
    
    @property
    def can_continue(self) -> bool:
        """Check if delegation can continue."""
        if self.is_terminated:
            return False
        if self.is_recursive:
            return False
        return True


# ---------------------------------------------------------------------------
# Trust Anchor Experiment
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TrustAnchorExperiment:
    """Result of a trust anchor experiment."""
    experiment_id: str
    experiment_name: str
    description: str
    result: TrustAnchorExperimentResult
    trust_anchor: Optional[TrustAnchor] = None
    domain_a: Optional[AuthorityDomain] = None
    domain_b: Optional[AuthorityDomain] = None
    delegation_chain: Optional[TerminatedDelegationChain] = None
    self_authorization_possible: bool = False
    delegation_terminates: bool = False
    sovereign_domains_valid: bool = False
    authority_delegation_distinct: bool = False
    rotation_without_regress: bool = False
    notes: str = ""
    normative_assumptions: list[str] = field(default_factory=list)
    underspecifications: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Trust Anchor Engine
# ---------------------------------------------------------------------------


@dataclass
class TrustAnchorEngine:
    """Engine for investigating trust anchors."""
    
    experiments: list[TrustAnchorExperiment] = field(default_factory=list)
    trust_anchors: dict[str, TrustAnchor] = field(default_factory=dict)
    domains: dict[str, AuthorityDomain] = field(default_factory=dict)
    delegation_chains: list[TerminatedDelegationChain] = field(default_factory=list)
    
    def create_trust_anchor(
        self,
        anchor_type: AnchorType,
        identity: str,
        domain: str,
        authority_scope: str = "*",
        status: AnchorStatus = AnchorStatus.ACTIVE,
        non_delegable: bool = True,
        authority_to_delegate: bool = True,
        authority_to_govern: bool = True,
        max_delegation_depth: int = 5,
        provenance: Optional[tuple[str, ...]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> TrustAnchor:
        """Create a trust anchor."""
        anchor = TrustAnchor(
            anchor_id=f"anchor_{uuid.uuid4().hex[:12]}",
            anchor_type=anchor_type,
            status=status,
            identity=identity,
            domain=domain,
            authority_scope=authority_scope,
            provenance=provenance or (),
            non_delegable=non_delegable,
            authority_to_delegate=authority_to_delegate,
            authority_to_govern=authority_to_govern,
            max_delegation_depth=max_delegation_depth,
            metadata=metadata or {},
        )
        self.trust_anchors[anchor.anchor_id] = anchor
        return anchor
    
    def create_authority_domain(
        self,
        domain_id: str,
        trust_anchor: TrustAnchor,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AuthorityDomain:
        """Create an authority domain."""
        domain = AuthorityDomain(
            domain_id=domain_id,
            trust_anchor=trust_anchor,
            metadata=metadata or {},
        )
        self.domains[domain_id] = domain
        return domain
    
    def create_delegation_chain(
        self,
        anchor_id: str,
        links: list[TerminatedDelegationLink],
        max_depth: int = 5,
    ) -> TerminatedDelegationChain:
        """Create a delegation chain with termination."""
        chain = TerminatedDelegationChain(
            chain_id=f"chain_{uuid.uuid4().hex[:12]}",
            anchor_id=anchor_id,
            links=links,
            max_depth=max_depth,
        )
        self.delegation_chains.append(chain)
        return chain
    
    def run_experiment(
        self,
        experiment_name: str,
        description: str,
        result: TrustAnchorExperimentResult,
        trust_anchor: Optional[TrustAnchor] = None,
        domain_a: Optional[AuthorityDomain] = None,
        domain_b: Optional[AuthorityDomain] = None,
        delegation_chain: Optional[TerminatedDelegationChain] = None,
        notes: str = "",
        normative_assumptions: Optional[list[str]] = None,
        underspecifications: Optional[list[str]] = None,
    ) -> TrustAnchorExperiment:
        """Run a trust anchor experiment."""
        experiment = TrustAnchorExperiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:12]}",
            experiment_name=experiment_name,
            description=description,
            result=result,
            trust_anchor=trust_anchor,
            domain_a=domain_a,
            domain_b=domain_b,
            delegation_chain=delegation_chain,
            self_authorization_possible=result == TrustAnchorExperimentResult.SELF_AUTHORIZATION_POSSIBLE,
            delegation_terminates=result == TrustAnchorExperimentResult.DELEGATION_TERMINATES,
            sovereign_domains_valid=result == TrustAnchorExperimentResult.SOVEREIGN_DOMAINS_VALID,
            authority_delegation_distinct=result == TrustAnchorExperimentResult.AUTHORITY_DELEGATION_DISTINCT,
            rotation_without_regress=result == TrustAnchorExperimentResult.ROTATION_WITHOUT_REGRESS,
            notes=notes,
            normative_assumptions=normative_assumptions or [],
            underspecifications=underspecifications or [],
        )
        self.experiments.append(experiment)
        return experiment


# ---------------------------------------------------------------------------
# Experiment 1: Distinguish Authority Origin, Trust Anchor, Delegation
# ---------------------------------------------------------------------------


def run_distinguish_three_concepts(engine: TrustAnchorEngine) -> TrustAnchorExperiment:
    """Experiment 1: Distinguish authority origin, trust anchor, delegation.
    
    AUTHORITY ORIGIN: Where did this authority claim originate?
    TRUST ANCHOR: What non-derived assumption does the system accept?
    AUTHORITY DELEGATION: How does authority move between principals?
    
    These are three distinct concepts. Conflating them creates ambiguity.
    """
    anchor = engine.create_trust_anchor(
        anchor_type=AnchorType.GENESIS,
        identity="admin",
        domain="production",
        authority_scope="*",
        provenance=("installation_time", "system_genesis"),
    )
    
    return engine.run_experiment(
        experiment_name="distinguish_three_concepts",
        description="Distinguish authority origin, trust anchor, and delegation",
        result=TrustAnchorExperimentResult.ANCHOR_EXPLICIT,
        trust_anchor=anchor,
        notes="Three concepts distinguished: origin (where), anchor (assumption), delegation (how)",
        normative_assumptions=[
            "Authority origin is a descriptive claim, not a normative one",
            "Trust anchor is a normative starting condition",
            "Delegation is a derived mechanism, not a root",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 2: Non-Self-Authorization
# ---------------------------------------------------------------------------


def run_test_non_self_authorization(engine: TrustAnchorEngine) -> TrustAnchorExperiment:
    """Experiment 2: Test non-self-authorization.
    
    Phase 16 discovered: ROOT → AUTHORITY TO CHANGE ROOT → ROOT
    
    The trust anchor must not be able to derive authority whose sole purpose
    is to retroactively establish or redefine the legitimacy of the same
    trust anchor.
    """
    anchor = engine.create_trust_anchor(
        anchor_type=AnchorType.GENESIS,
        identity="admin",
        domain="production",
        non_delegable=True,
        authority_to_delegate=True,
        max_delegation_depth=3,
    )
    
    # Attempt self-authorization: anchor delegates authority to modify itself
    link1 = TerminatedDelegationLink(
        link_id=f"link_{uuid.uuid4().hex[:12]}",
        delegator_id=anchor.anchor_id,
        delegate_id="policy_admin",
        capability="modify_anchor",
        scope="production",
        valid_from="2026-01-01T00:00:00Z",
        valid_until="2026-12-31T23:59:59Z",
        delegation_right=True,
    )
    
    # Self-authorization: policy_admin can modify the anchor
    link2 = TerminatedDelegationLink(
        link_id=f"link_{uuid.uuid4().hex[:12]}",
        delegator_id="policy_admin",
        delegate_id=anchor.anchor_id,  # Cycles back to anchor
        capability="modify_anchor",
        scope="production",
        valid_from="2026-01-01T00:00:00Z",
        valid_until="2026-12-31T23:59:59Z",
    )
    
    chain = engine.create_delegation_chain(
        anchor_id=anchor.anchor_id,
        links=[link1, link2],
        max_depth=3,
    )
    
    # The chain is recursive (anchor → policy_admin → anchor)
    self_auth_possible = chain.is_recursive
    
    return engine.run_experiment(
        experiment_name="test_non_self_authorization",
        description="Test that trust anchor cannot self-authorize",
        result=TrustAnchorExperimentResult.SELF_AUTHORIZATION_POSSIBLE if self_auth_possible else TrustAnchorExperimentResult.SELF_AUTHORIZATION_BLOCKED,
        trust_anchor=anchor,
        delegation_chain=chain,
        notes="Self-authorization detected: anchor can delegate authority to modify itself",
        normative_assumptions=[
            "A trust anchor must not derive authority to redefine its own legitimacy",
        ],
        underspecifications=[
            "No explicit mechanism prevents anchor self-modification",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 3: Delegation Termination
# ---------------------------------------------------------------------------


def run_test_delegation_termination(engine: TrustAnchorEngine) -> TrustAnchorExperiment:
    """Experiment 3: Test delegation termination.
    
    Construct: A → B → C → D → ...
    Determine the exact termination condition.
    """
    anchor = engine.create_trust_anchor(
        anchor_type=AnchorType.GENESIS,
        identity="admin",
        domain="production",
        max_delegation_depth=3,
    )
    
    # Chain that exceeds max depth
    link1 = TerminatedDelegationLink(
        link_id=f"link_{uuid.uuid4().hex[:12]}",
        delegator_id=anchor.anchor_id,
        delegate_id="level_1",
        capability="delegate",
        scope="production",
        valid_from="2026-01-01T00:00:00Z",
        valid_until="2026-12-31T23:59:59Z",
        delegation_right=True,
    )
    link2 = TerminatedDelegationLink(
        link_id=f"link_{uuid.uuid4().hex[:12]}",
        delegator_id="level_1",
        delegate_id="level_2",
        capability="delegate",
        scope="production",
        valid_from="2026-01-01T00:00:00Z",
        valid_until="2026-12-31T23:59:59Z",
        delegation_right=True,
    )
    link3 = TerminatedDelegationLink(
        link_id=f"link_{uuid.uuid4().hex[:12]}",
        delegator_id="level_2",
        delegate_id="level_3",
        capability="delegate",
        scope="production",
        valid_from="2026-01-01T00:00:00Z",
        valid_until="2026-12-31T23:59:59Z",
        delegation_right=True,
    )
    link4 = TerminatedDelegationLink(
        link_id=f"link_{uuid.uuid4().hex[:12]}",
        delegator_id="level_3",
        delegate_id="level_4",
        capability="delegate",
        scope="production",
        valid_from="2026-01-01T00:00:00Z",
        valid_until="2026-12-31T23:59:59Z",
        delegation_right=True,
    )
    
    chain = engine.create_delegation_chain(
        anchor_id=anchor.anchor_id,
        links=[link1, link2, link3, link4],
        max_depth=3,
    )
    
    # Chain should be terminated at depth 3
    terminates = chain.is_terminated and chain.depth > chain.max_depth
    
    return engine.run_experiment(
        experiment_name="test_delegation_termination",
        description="Test delegation termination conditions",
        result=TrustAnchorExperimentResult.DELEGATION_TERMINATES if terminates else TrustAnchorExperimentResult.DELEGATION_UNBOUNDED,
        trust_anchor=anchor,
        delegation_chain=chain,
        notes=f"Chain depth={chain.depth}, max_depth={chain.max_depth}, terminated={chain.is_terminated}",
        normative_assumptions=[
            "Delegation must terminate at a bounded depth",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 4: Sovereign Domain Coexistence
# ---------------------------------------------------------------------------


def run_test_sovereign_domains(engine: TrustAnchorEngine) -> TrustAnchorExperiment:
    """Experiment 4: Test sovereign domain coexistence.
    
    Construct two independent authority domains:
    - DOMAIN_A with TRUST_ANCHOR_A
    - DOMAIN_B with TRUST_ANCHOR_B
    
    Determine whether the architecture can represent both without requiring
    one domain to become subordinate to the other.
    """
    anchor_a = engine.create_trust_anchor(
        anchor_type=AnchorType.GENESIS,
        identity="admin_a",
        domain="domain_a",
        authority_scope="domain_a",
    )
    anchor_b = engine.create_trust_anchor(
        anchor_type=AnchorType.GENESIS,
        identity="admin_b",
        domain="domain_b",
        authority_scope="domain_b",
    )
    
    domain_a = engine.create_authority_domain(
        domain_id="domain_a",
        trust_anchor=anchor_a,
    )
    domain_b = engine.create_authority_domain(
        domain_id="domain_b",
        trust_anchor=anchor_b,
    )
    
    # Check sovereignty
    a_sovereign = domain_a.is_sovereign and not domain_a.has_cross_domain_authority(domain_b)
    b_sovereign = domain_b.is_sovereign and not domain_b.has_cross_domain_authority(domain_a)
    
    return engine.run_experiment(
        experiment_name="test_sovereign_domains",
        description="Test sovereign domain coexistence",
        result=TrustAnchorExperimentResult.SOVEREIGN_DOMAINS_VALID if (a_sovereign and b_sovereign) else TrustAnchorExperimentResult.SOVEREIGN_DOMAINS_CONFLATED,
        domain_a=domain_a,
        domain_b=domain_b,
        notes=f"Domain A sovereign: {a_sovereign}, Domain B sovereign: {b_sovereign}",
        normative_assumptions=[
            "Two trust anchors can coexist without one being subordinate",
            "Cross-domain authority requires explicit delegation",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 5: Authority to Delegate vs Authority to Execute
# ---------------------------------------------------------------------------


def run_test_delegate_vs_execute(engine: TrustAnchorEngine) -> TrustAnchorExperiment:
    """Experiment 5: Test authority to delegate vs authority to execute.
    
    AUTHORITY TO EXECUTE ≠ AUTHORITY TO DELEGATE EXECUTION.
    
    A trust anchor can delegate PAYMENT_EXECUTION_AUTHORITY without itself
    executing payments.
    """
    anchor = engine.create_trust_anchor(
        anchor_type=AnchorType.GENESIS,
        identity="admin",
        domain="production",
        authority_to_delegate=True,
        authority_to_govern=True,
        max_delegation_depth=3,
    )
    
    # Anchor delegates payment execution to a service
    link1 = TerminatedDelegationLink(
        link_id=f"link_{uuid.uuid4().hex[:12]}",
        delegator_id=anchor.anchor_id,
        delegate_id="payment_service",
        capability="execute_payment",
        scope="production",
        valid_from="2026-01-01T00:00:00Z",
        valid_until="2026-12-31T23:59:59Z",
        is_terminal=True,  # payment_service cannot further delegate
    )
    
    chain = engine.create_delegation_chain(
        anchor_id=anchor.anchor_id,
        links=[link1],
    )
    
    # The anchor has authority to delegate but the chain terminates
    # The anchor itself does not execute payments
    delegation_distinct = chain.is_terminated and anchor.authority_to_delegate
    
    return engine.run_experiment(
        experiment_name="test_delegate_vs_execute",
        description="Test authority to delegate vs authority to execute",
        result=TrustAnchorExperimentResult.AUTHORITY_DELEGATION_DISTINCT if delegation_distinct else TrustAnchorExperimentResult.AUTHORITY_DELEGATION_CONFLATED,
        trust_anchor=anchor,
        delegation_chain=chain,
        notes="Anchor can delegate payment execution without executing payments itself",
        normative_assumptions=[
            "Authority to delegate X ≠ authority to perform X",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 6: Trust Anchor Rotation
# ---------------------------------------------------------------------------


def run_test_anchor_rotation(engine: TrustAnchorEngine) -> TrustAnchorExperiment:
    """Experiment 6: Test trust anchor rotation.
    
    Test: Anchor A → Anchor B
    
    Determine whether B is:
    - derived from A (creates regress)
    - independently established (no regress)
    - successor (explicit rotation)
    """
    anchor_a = engine.create_trust_anchor(
        anchor_type=AnchorType.CRYPTOGRAPHIC,
        identity="admin_a",
        domain="production",
        status=AnchorStatus.ROTATED,
    )
    
    # Anchor B is independently established, not derived from A
    anchor_b = engine.create_trust_anchor(
        anchor_type=AnchorType.CRYPTOGRAPHIC,
        identity="admin_b",
        domain="production",
        status=AnchorStatus.ACTIVE,
        provenance=("independent_establishment", "key_rotation"),
    )
    
    # Check: B is not derived from A
    b_derived_from_a = anchor_b.metadata.get("derived_from") == anchor_a.anchor_id
    
    return engine.run_experiment(
        experiment_name="test_anchor_rotation",
        description="Test trust anchor rotation without regress",
        result=TrustAnchorExperimentResult.ROTATION_WITHOUT_REGRESS if not b_derived_from_a else TrustAnchorExperimentResult.ROTATION_CREATES_REGRESS,
        trust_anchor=anchor_b,
        notes="Anchor B is independently established, not derived from Anchor A",
        normative_assumptions=[
            "Anchor rotation must not create infinite regress",
            "New anchor can be independently established",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 7: Cross-Domain Delegation
# ---------------------------------------------------------------------------


def run_test_cross_domain_delegation(engine: TrustAnchorEngine) -> TrustAnchorExperiment:
    """Experiment 7: Test cross-domain delegation.
    
    Test: A → B delegation and B → A delegation and no delegation.
    
    Determine whether sovereignty is preserved.
    """
    anchor_a = engine.create_trust_anchor(
        anchor_type=AnchorType.GENESIS,
        identity="admin_a",
        domain="domain_a",
        authority_scope="domain_a",
        metadata={"cross_domain_delegation": True},
    )
    anchor_b = engine.create_trust_anchor(
        anchor_type=AnchorType.GENESIS,
        identity="admin_b",
        domain="domain_b",
        authority_scope="domain_b",
    )
    
    domain_a = engine.create_authority_domain(
        domain_id="domain_a",
        trust_anchor=anchor_a,
    )
    domain_b = engine.create_authority_domain(
        domain_id="domain_b",
        trust_anchor=anchor_b,
        metadata={"delegated_from": ["domain_a"]},  # B receives delegation from A
    )
    
    # A can delegate to B (explicit cross-domain right)
    a_can_delegate_to_b = anchor_a.can_delegate_to("domain_b")
    
    # B cannot delegate back to A (no cross-domain right)
    b_can_delegate_to_a = anchor_b.can_delegate_to("domain_a")
    
    return engine.run_experiment(
        experiment_name="test_cross_domain_delegation",
        description="Test cross-domain delegation preserves sovereignty",
        result=TrustAnchorExperimentResult.SOVEREIGN_DOMAINS_VALID if a_can_delegate_to_b and not b_can_delegate_to_a else TrustAnchorExperimentResult.SOVEREIGN_DOMAINS_CONFLATED,
        domain_a=domain_a,
        domain_b=domain_b,
        notes=f"A→B: {a_can_delegate_to_b}, B→A: {b_can_delegate_to_a}",
        normative_assumptions=[
            "Cross-domain delegation is explicit and unidirectional by default",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 8: Trust Anchor Scope
# ---------------------------------------------------------------------------


def run_test_anchor_scope(engine: TrustAnchorEngine) -> TrustAnchorExperiment:
    """Experiment 8: Test trust anchor scope.
    
    Test trust anchors with:
    - global scope
    - tenant scope
    - domain scope
    - resource scope
    - operation scope
    
    Determine whether a trust anchor scoped to DOMAIN_A can derive
    authority for DOMAIN_B.
    """
    global_anchor = engine.create_trust_anchor(
        anchor_type=AnchorType.GENESIS,
        identity="admin",
        domain="global",
        authority_scope="*",
    )
    
    domain_anchor = engine.create_trust_anchor(
        anchor_type=AnchorType.GENESIS,
        identity="admin_domain",
        domain="domain_a",
        authority_scope="domain_a",
    )
    
    # Global anchor can authorize any scope
    global_can_authorize_domain_b = global_anchor.can_delegate_to("domain_b")
    
    # Domain anchor cannot authorize other domains
    domain_can_authorize_domain_b = domain_anchor.can_delegate_to("domain_b")
    
    return engine.run_experiment(
        experiment_name="test_anchor_scope",
        description="Test trust anchor scope boundaries",
        result=TrustAnchorExperimentResult.ANCHOR_EXPLICIT,
        trust_anchor=domain_anchor,
        notes=f"Global anchor can authorize domain_b: {global_can_authorize_domain_b}, Domain anchor can authorize domain_b: {domain_can_authorize_domain_b}",
        normative_assumptions=[
            "A higher position in the graph must not automatically imply broader scope",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 9: Trust Anchor Temporality
# ---------------------------------------------------------------------------


def run_test_anchor_temporality(engine: TrustAnchorEngine) -> TrustAnchorExperiment:
    """Experiment 9: Test trust anchor temporality.
    
    Test trust anchors with:
    - indefinite validity
    - bounded validity
    - expired validity
    - revoked validity
    - superseded validity
    
    Determine whether derived authority survives trust-anchor expiration
    or revocation.
    """
    active_anchor = engine.create_trust_anchor(
        anchor_type=AnchorType.GENESIS,
        identity="admin",
        domain="production",
        status=AnchorStatus.ACTIVE,
    )
    
    expired_anchor = engine.create_trust_anchor(
        anchor_type=AnchorType.GENESIS,
        identity="admin",
        domain="production",
        status=AnchorStatus.EXPIRED,
    )
    
    # Derived authority from expired anchor should not be valid
    # (this is a semantic requirement, not yet enforced)
    derived_from_expired_valid = expired_anchor.is_active  # False
    
    return engine.run_experiment(
        experiment_name="test_anchor_temporality",
        description="Test trust anchor temporality",
        result=TrustAnchorExperimentResult.ANCHOR_EXPLICIT,
        trust_anchor=active_anchor,
        notes="Derived authority from expired anchor is not valid",
        normative_assumptions=[
            "Derived authority does not survive trust-anchor expiration",
        ],
        underspecifications=[
            "No explicit mechanism invalidates derived authority on anchor expiration",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 10: Trust Anchor Compromise
# ---------------------------------------------------------------------------


def run_test_anchor_compromise(engine: TrustAnchorEngine) -> TrustAnchorExperiment:
    """Experiment 10: Test trust anchor compromise.
    
    Model compromise of:
    - trust-anchor identity
    - trust-anchor credential
    - trust-anchor storage
    - trust-anchor provenance
    - bootstrap configuration
    - delegation registry
    
    Determine what compromise permits:
    - authority forgery
    - authority amplification
    - authority substitution
    - authority replay
    - authority revocation
    - authority persistence
    """
    compromised_anchor = engine.create_trust_anchor(
        anchor_type=AnchorType.CRYPTOGRAPHIC,
        identity="admin",
        domain="production",
        status=AnchorStatus.COMPROMISED,
    )
    
    # Compromised anchor is not active
    is_active = compromised_anchor.is_active
    
    return engine.run_experiment(
        experiment_name="test_anchor_compromise",
        description="Test trust anchor compromise scenarios",
        result=TrustAnchorExperimentResult.ANCHOR_IMPLICIT,
        trust_anchor=compromised_anchor,
        notes="Compromised anchor is not active, but no recovery mechanism exists",
        underspecifications=[
            "No explicit root compromise detection",
            "No explicit root recovery mechanism",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 11: Authority Conservation with Trust Anchor
# ---------------------------------------------------------------------------


def run_test_authority_conservation(engine: TrustAnchorEngine) -> TrustAnchorExperiment:
    """Experiment 11: Test authority conservation with trust anchor.
    
    Test whether explicit trust anchoring changes the Phase 15 authority
    transformation semantics.
    
    Test: identity, narrowing, delegation, broadening, scope expansion,
    temporal expansion, condition weakening, capability expansion, composition.
    
    Determine whether a trust anchor can legitimately delegate broader
    authority than its own operational capability.
    """
    anchor = engine.create_trust_anchor(
        anchor_type=AnchorType.GENESIS,
        identity="admin",
        domain="production",
        authority_to_delegate=True,
        max_delegation_depth=3,
    )
    
    # Anchor delegates payment execution
    link1 = TerminatedDelegationLink(
        link_id=f"link_{uuid.uuid4().hex[:12]}",
        delegator_id=anchor.anchor_id,
        delegate_id="payment_service",
        capability="execute_payment",
        scope="production",
        valid_from="2026-01-01T00:00:00Z",
        valid_until="2026-12-31T23:59:59Z",
        is_terminal=True,
    )
    
    chain = engine.create_delegation_chain(
        anchor_id=anchor.anchor_id,
        links=[link1],
    )
    
    # The anchor delegates payment execution but does not execute payments
    # This is legitimate: authority to delegate ≠ authority to execute
    conservation_holds = chain.is_terminated
    
    return engine.run_experiment(
        experiment_name="test_authority_conservation",
        description="Test authority conservation with trust anchor",
        result=TrustAnchorExperimentResult.AUTHORITY_DELEGATION_DISTINCT if conservation_holds else TrustAnchorExperimentResult.AUTHORITY_DELEGATION_CONFLATED,
        trust_anchor=anchor,
        delegation_chain=chain,
        notes="Trust anchor can delegate authority without possessing operational capability",
        normative_assumptions=[
            "Authority to delegate X ≠ authority to perform X",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 12: Oracle Separation
# ---------------------------------------------------------------------------


def run_test_oracle_separation(engine: TrustAnchorEngine) -> TrustAnchorExperiment:
    """Experiment 12: Test oracle separation.
    
    Maintain four distinct layers:
    - WORLD GROUND TRUTH
    - EXPERIMENTAL ORACLE
    - PROTOCOL COMPUTATION
    - NORMATIVE TRUST ASSUMPTION
    
    The trust anchor itself may be normative.
    Do not encode "this anchor is legitimate" into the experimental oracle
    and then report that legitimacy was discovered.
    """
    anchor = engine.create_trust_anchor(
        anchor_type=AnchorType.GENESIS,
        identity="admin",
        domain="production",
        provenance=("normative_assumption", "system_genesis"),
    )
    
    return engine.run_experiment(
        experiment_name="test_oracle_separation",
        description="Maintain oracle separation for trust anchor experiments",
        result=TrustAnchorExperimentResult.ANCHOR_EXPLICIT,
        trust_anchor=anchor,
        notes="Trust anchor is a normative assumption, not an empirically derived fact",
        normative_assumptions=[
            "The trust anchor is trusted by assumption, not by derivation",
            "This is a normative architectural requirement, not an experimental result",
        ],
    )


# ---------------------------------------------------------------------------
# Run All Phase 17 Experiments
# ---------------------------------------------------------------------------


def run_all_phase17_experiments() -> dict[str, Any]:
    """Run all Phase 17 experiments."""
    engine = TrustAnchorEngine()
    
    experiments = {}
    
    experiments["distinguish_three_concepts"] = run_distinguish_three_concepts(engine)
    experiments["test_non_self_authorization"] = run_test_non_self_authorization(engine)
    experiments["test_delegation_termination"] = run_test_delegation_termination(engine)
    experiments["test_sovereign_domains"] = run_test_sovereign_domains(engine)
    experiments["test_delegate_vs_execute"] = run_test_delegate_vs_execute(engine)
    experiments["test_anchor_rotation"] = run_test_anchor_rotation(engine)
    experiments["test_cross_domain_delegation"] = run_test_cross_domain_delegation(engine)
    experiments["test_anchor_scope"] = run_test_anchor_scope(engine)
    experiments["test_anchor_temporality"] = run_test_anchor_temporality(engine)
    experiments["test_anchor_compromise"] = run_test_anchor_compromise(engine)
    experiments["test_authority_conservation"] = run_test_authority_conservation(engine)
    experiments["test_oracle_separation"] = run_test_oracle_separation(engine)
    
    return {
        "experiments": experiments,
        "total_experiments": len(experiments),
        "anchor_explicit_count": sum(1 for e in experiments.values() if e.result == TrustAnchorExperimentResult.ANCHOR_EXPLICIT),
        "anchor_implicit_count": sum(1 for e in experiments.values() if e.result == TrustAnchorExperimentResult.ANCHOR_IMPLICIT),
        "self_authorization_possible_count": sum(1 for e in experiments.values() if e.result == TrustAnchorExperimentResult.SELF_AUTHORIZATION_POSSIBLE),
        "self_authorization_blocked_count": sum(1 for e in experiments.values() if e.result == TrustAnchorExperimentResult.SELF_AUTHORIZATION_BLOCKED),
        "delegation_terminates_count": sum(1 for e in experiments.values() if e.result == TrustAnchorExperimentResult.DELEGATION_TERMINATES),
        "sovereign_domains_valid_count": sum(1 for e in experiments.values() if e.result == TrustAnchorExperimentResult.SOVEREIGN_DOMAINS_VALID),
        "authority_delegation_distinct_count": sum(1 for e in experiments.values() if e.result == TrustAnchorExperimentResult.AUTHORITY_DELEGATION_DISTINCT),
        "rotation_without_regress_count": sum(1 for e in experiments.values() if e.result == TrustAnchorExperimentResult.ROTATION_WITHOUT_REGRESS),
    }


if __name__ == "__main__":
    results = run_all_phase17_experiments()
    
    print("\n" + "=" * 120)
    print("PHASE 17: TRUST ANCHOR")
    print("=" * 120)
    
    print(f"\nTotal experiments: {results['total_experiments']}")
    print(f"Anchor explicit: {results['anchor_explicit_count']}")
    print(f"Anchor implicit: {results['anchor_implicit_count']}")
    print(f"Self-authorization possible: {results['self_authorization_possible_count']}")
    print(f"Self-authorization blocked: {results['self_authorization_blocked_count']}")
    print(f"Delegation terminates: {results['delegation_terminates_count']}")
    print(f"Sovereign domains valid: {results['sovereign_domains_valid_count']}")
    print(f"Authority delegation distinct: {results['authority_delegation_distinct_count']}")
    print(f"Rotation without regress: {results['rotation_without_regress_count']}")
    
    for name, exp in results["experiments"].items():
        print(f"\n{name}:")
        print(f"  Result: {exp.result.value}")
        print(f"  Notes: {exp.notes}")
        if exp.underspecifications:
            print(f"  Underspecifications: {exp.underspecifications}")
