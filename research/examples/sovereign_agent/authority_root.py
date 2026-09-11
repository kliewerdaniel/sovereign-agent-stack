"""Phase 16: Authority Root.

Investigates what terminates the authority chain.

Phase 15 established EFFECT_BOUNDARY_ESTABLISHED: an actor with legitimate
policy modification authority can construct policies whose downstream
authority exceeds the actor's legitimate authority, and even explicit
meta-authority must be bounded by an envelope.

Phase 16 asks: WHAT TERMINATES THE AUTHORITY CHAIN?

The central question:

What is the irreducible source from which authority is ultimately derived?

Do not invent a philosophical answer. Trace the implementation.

Existing infrastructure reused:
- AuthorityRoot, RootType, ProtocolDomain (protocol_lineage.py)
- AuthorityClosure, ClosureStatus (compositional_authority.py)
- RuntimeAuthorityGate (runtime_authority_gate.py)
- PolicyGovernanceEngine, PolicyAuthorityRecord (policy_governance.py)
- AuthoritySurface, AuthorityEnvelope (effect_boundary.py)
- ConsequentialAuthority, ConditionalAuthority (consequential_authority.py)
- DelegationArtifact (compositional_authority.py)
- EpistemicCycleDetector, CycleType (epistemic_cycles.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Authority Root Types
# ---------------------------------------------------------------------------


class AuthorityRootType(str, Enum):
    """Types of authority roots.
    
    The architecture distinguishes four root types.
    """
    AUTHORITY = "authority"
    IDENTITY = "identity"
    POLICY = "policy"
    PROVENANCE = "provenance"


class RootStatus(str, Enum):
    """Status of an authority root."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ROTATED = "rotated"
    COMPROMISED = "compromised"
    GENESIS = "genesis"


class RootMutationType(str, Enum):
    """Types of mutations to an authority root."""
    MODIFY = "modify"
    REPLACE = "replace"
    DELETE = "delete"
    REVOKE = "revoke"
    FORK = "fork"
    DUPLICATE = "duplicate"
    DELEGATE = "delegate"
    EXPIRE = "expire"
    ROLLBACK = "rollback"
    RESTORE = "restore"


class AuthorityRootExperimentResult(str, Enum):
    """Result of an authority root experiment."""
    ROOT_EXPLICIT = "root_explicit"
    ROOT_IMPLICIT = "root_implicit"
    ROOT_UNDERSPECIFIED = "root_underspecified"
    SELF_CREATION = "self_creation"
    AMPLIFICATION_AT_ROOT = "amplification_at_root"
    DELEGATION_TERMINATES = "delegation_terminates"
    DELEGATION_RECURSIVE = "delegation_recursive"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Authority Root Record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityRootRecord:
    """A record of an authority root.
    
    An authority root is the irreducible source from which authority
    is ultimately derived. It is NOT derived from another authority.
    """
    root_id: str
    root_type: AuthorityRootType
    status: RootStatus
    established_at: str
    expires_at: str = "-1"
    principal: str = ""
    scope: str = "*"
    derivation_basis: str = ""  # How this root was established
    is_derived: bool = False  # True if derived from another root
    parent_root_id: Optional[str] = None
    provenance: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_genesis(self) -> bool:
        """Check if this is a genesis root (not derived from anything)."""
        return not self.is_derived and self.status == RootStatus.GENESIS
    
    @property
    def is_active(self) -> bool:
        """Check if this root is currently active."""
        return self.status in (RootStatus.ACTIVE, RootStatus.GENESIS)
    
    def can_authorize(self, scope: str) -> bool:
        """Check if this root can authorize a given scope."""
        if not self.is_active:
            return False
        if self.scope != "*" and self.scope != scope:
            return False
        return True


# ---------------------------------------------------------------------------
# Delegation Chain
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationLink:
    """A single link in a delegation chain."""
    link_id: str
    delegator_id: str
    delegate_id: str
    capability: str
    scope: str
    valid_from: str
    valid_until: str
    is_terminal: bool = False  # True if this is the last link
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class DelegationChain:
    """A chain of delegations from root to execution."""
    chain_id: str
    root_id: str
    links: list[DelegationLink]
    terminal_authority: str = ""
    
    @property
    def depth(self) -> int:
        """Get the depth of the chain."""
        return len(self.links)
    
    @property
    def is_terminated(self) -> bool:
        """Check if the chain is terminated."""
        if not self.links:
            return True
        return self.links[-1].is_terminal
    
    @property
    def is_recursive(self) -> bool:
        """Check if the chain is recursive (cycles back to root)."""
        if not self.links:
            return False
        delegate_ids = [link.delegate_id for link in self.links]
        return len(delegate_ids) != len(set(delegate_ids))


# ---------------------------------------------------------------------------
# Authority Root Experiment
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityRootExperiment:
    """Result of an authority root experiment."""
    experiment_id: str
    experiment_name: str
    description: str
    result: AuthorityRootExperimentResult
    root_record: Optional[AuthorityRootRecord]
    delegation_chain: Optional[DelegationChain]
    authority_amplified: bool
    self_creation_detected: bool
    recursion_detected: bool
    notes: str = ""
    normative_assumptions: list[str] = field(default_factory=list)
    underspecifications: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Authority Root Engine
# ---------------------------------------------------------------------------


@dataclass
class AuthorityRootEngine:
    """Engine for investigating authority roots."""
    
    experiments: list[AuthorityRootExperiment] = field(default_factory=list)
    root_records: dict[str, AuthorityRootRecord] = field(default_factory=dict)
    delegation_chains: list[DelegationChain] = field(default_factory=list)
    
    def create_root_record(
        self,
        root_type: AuthorityRootType,
        status: RootStatus = RootStatus.ACTIVE,
        principal: str = "",
        scope: str = "*",
        derivation_basis: str = "",
        is_derived: bool = False,
        parent_root_id: Optional[str] = None,
        provenance: Optional[tuple[str, ...]] = None,
    ) -> AuthorityRootRecord:
        """Create a new authority root record."""
        record = AuthorityRootRecord(
            root_id=f"root_{uuid.uuid4().hex[:12]}",
            root_type=root_type,
            status=status,
            established_at="2026-01-01T00:00:00Z",
            principal=principal,
            scope=scope,
            derivation_basis=derivation_basis,
            is_derived=is_derived,
            parent_root_id=parent_root_id,
            provenance=provenance or (),
        )
        self.root_records[record.root_id] = record
        return record
    
    def create_delegation_chain(
        self,
        root_id: str,
        links: list[DelegationLink],
        terminal_authority: str = "",
    ) -> DelegationChain:
        """Create a delegation chain."""
        chain = DelegationChain(
            chain_id=f"chain_{uuid.uuid4().hex[:12]}",
            root_id=root_id,
            links=links,
            terminal_authority=terminal_authority,
        )
        self.delegation_chains.append(chain)
        return chain
    
    def run_experiment(
        self,
        experiment_name: str,
        description: str,
        root_record: Optional[AuthorityRootRecord] = None,
        delegation_chain: Optional[DelegationChain] = None,
        notes: str = "",
        normative_assumptions: Optional[list[str]] = None,
        underspecifications: Optional[list[str]] = None,
    ) -> AuthorityRootExperiment:
        """Run an authority root experiment."""
        # Determine result
        authority_amplified = False
        self_creation_detected = False
        recursion_detected = False
        
        if delegation_chain is not None:
            recursion_detected = delegation_chain.is_recursive
            if recursion_detected:
                result = AuthorityRootExperimentResult.DELEGATION_RECURSIVE
            elif not delegation_chain.is_terminated:
                result = AuthorityRootExperimentResult.ROOT_UNDERSPECIFIED
            else:
                result = AuthorityRootExperimentResult.DELEGATION_TERMINATES
        elif root_record is not None:
            if root_record.is_genesis:
                result = AuthorityRootExperimentResult.ROOT_EXPLICIT
            elif root_record.is_derived:
                self_creation_detected = True
                result = AuthorityRootExperimentResult.SELF_CREATION
            else:
                result = AuthorityRootExperimentResult.ROOT_IMPLICIT
        else:
            result = AuthorityRootExperimentResult.UNKNOWN
        
        experiment = AuthorityRootExperiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:12]}",
            experiment_name=experiment_name,
            description=description,
            result=result,
            root_record=root_record,
            delegation_chain=delegation_chain,
            authority_amplified=authority_amplified,
            self_creation_detected=self_creation_detected,
            recursion_detected=recursion_detected,
            notes=notes,
            normative_assumptions=normative_assumptions or [],
            underspecifications=underspecifications or [],
        )
        
        self.experiments.append(experiment)
        return experiment


# ---------------------------------------------------------------------------
# Experiment Implementations
# ---------------------------------------------------------------------------


def run_reconstruct_authority_graph(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 1: Reconstruct the complete authority graph.
    
    Trace: ROOT → DELEGATION → POLICY AUTHORITY → POLICY EFFECT AUTHORITY
           → GOVERNANCE → DOWNSTREAM AUTHORITY → CAPABILITY → EXECUTION
    """
    # The current implementation has AuthorityRoot in protocol_lineage.py
    # but the root is typically just a string identifier.
    # The actual root is the "admin" principal or a hardcoded bootstrap.
    
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        scope="*",
        derivation_basis="bootstrap_assertion",  # Not derived from anything
        is_derived=False,
        provenance=("system_genesis",),
    )
    
    return engine.run_experiment(
        experiment_name="reconstruct_authority_graph",
        description="Reconstruct the complete authority graph from implementation",
        root_record=root,
        notes="The current implementation has AuthorityRoot type but the root is typically a hardcoded bootstrap",
        underspecifications=[
            "The actual root is the 'admin' principal, not an explicit governance mechanism",
            "AuthorityRoot exists as a type but is not integrated into the governance chain",
        ],
    )


def run_distinguish_origin_from_representation(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 2: Distinguish authority origin from representation.
    
    PROVENANCE OF AUTHORITY ≠ SOURCE OF AUTHORITY.
    A cryptographic signature can prove who signed something.
    It does not by itself establish that the signer had legitimate authority.
    """
    # The current implementation uses content hashes and provenance chains
    # to represent authority, but the origin is still a bootstrap assumption.
    
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.ACTIVE,
        principal="admin",
        derivation_basis="cryptographic_signature",
        provenance=("signature_valid", "provenance_complete"),
    )
    
    return engine.run_experiment(
        experiment_name="distinguish_origin_from_representation",
        description="Distinguish authority origin from authority representation",
        root_record=root,
        notes="Cryptographic signatures prove authenticity but not authority origin",
        normative_assumptions=[
            "Provenance explains the effect without being mistaken for authority to produce the effect",
        ],
    )


def run_investigate_bootstrap_authority(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 3: Investigate bootstrap authority.
    
    Find every bootstrap mechanism: default principals, root keys,
    admin identities, initial policies, hard-coded authorities.
    """
    # The current implementation uses "admin" as the default principal
    # in policy_governance.py. This is the implicit bootstrap.
    
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        scope="*",
        derivation_basis="hardcoded_bootstrap",
        is_derived=False,
        provenance=("default_principal", "system_initialization"),
    )
    
    return engine.run_experiment(
        experiment_name="investigate_bootstrap_authority",
        description="Investigate bootstrap authority mechanisms",
        root_record=root,
        notes="The 'admin' principal is the implicit bootstrap authority in policy_governance.py",
        underspecifications=[
            "Bootstrap authority is hardcoded, not governed",
            "No explicit mechanism for rotating or revoking the bootstrap",
        ],
    )


def run_test_root_mutation(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 4: Test root authority mutation.
    
    Attempt: modify root, replace root, delete root, revoke root,
    fork root, duplicate root, delegate root, expire root,
    roll back root, restore old root state.
    """
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        derivation_basis="bootstrap",
    )
    
    return engine.run_experiment(
        experiment_name="test_root_mutation",
        description="Test root authority mutation operations",
        root_record=root,
        notes="Root mutation is not explicitly governed in the current implementation",
        underspecifications=[
            "No explicit mechanism for modifying the authority root",
            "Root rotation is not implemented",
        ],
    )


def run_test_root_self_authorization(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 5: Test root authority self-authorization.
    
    Attempt to construct: ROOT → AUTHORITY TO CHANGE ROOT → NEW ROOT
    
    Determine whether the system permits authority to recursively
    authorize itself.
    """
    # Create a root that authorizes itself
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        derivation_basis="self_authorizing",
        is_derived=True,  # Derived from itself
        parent_root_id="self",  # Points to itself
    )
    
    return engine.run_experiment(
        experiment_name="test_root_self_authorization",
        description="Test whether root authority can self-authorize",
        root_record=root,
        notes="Self-authorizing root detected — authority derivation cycles back to itself",
        normative_assumptions=[
            "Authority derivation should not cycle back to the same root",
        ],
    )


def run_investigate_termination_condition(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 6: Investigate the termination condition.
    
    If authority delegation is recursive:
    A → delegates B → B delegates C → C delegates D
    
    Determine what terminates the chain.
    """
    # Create a delegation chain that terminates at a non-delegable root
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        derivation_basis="non_delegable_root",
    )
    
    link1 = DelegationLink(
        link_id=f"link_{uuid.uuid4().hex[:12]}",
        delegator_id=root.root_id,
        delegate_id="policy_admin",
        capability="modify_policy",
        scope="production",
        valid_from="2026-01-01T00:00:00Z",
        valid_until="2026-12-31T23:59:59Z",
    )
    
    link2 = DelegationLink(
        link_id=f"link_{uuid.uuid4().hex[:12]}",
        delegator_id="policy_admin",
        delegate_id="governance_engine",
        capability="evaluate_policy",
        scope="production",
        valid_from="2026-01-01T00:00:00Z",
        valid_until="2026-12-31T23:59:59Z",
        is_terminal=True,  # Terminal link
    )
    
    chain = engine.create_delegation_chain(
        root_id=root.root_id,
        links=[link1, link2],
        terminal_authority="governance_engine",
    )
    
    return engine.run_experiment(
        experiment_name="investigate_termination_condition",
        description="Investigate what terminates the delegation chain",
        root_record=root,
        delegation_chain=chain,
        notes="The chain terminates at a non-delegable root, but the termination is not explicitly enforced",
        underspecifications=[
            "No explicit bounded delegation depth",
            "No explicit non-delegable root enforcement",
        ],
    )


def run_investigate_genesis_authority(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 7: Investigate genesis authority.
    
    Determine whether the architecture contains an implicit genesis authority.
    """
    genesis = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        scope="*",
        derivation_basis="genesis_state",
        is_derived=False,
        provenance=("system_genesis", "initial_configuration"),
    )
    
    return engine.run_experiment(
        experiment_name="investigate_genesis_authority",
        description="Investigate genesis authority in the architecture",
        root_record=genesis,
        notes="Genesis authority exists as the 'admin' principal with GENESIS status",
        underspecifications=[
            "Genesis authority is immutable in principle but not enforced",
            "No explicit mechanism for genesis authority recovery",
        ],
    )


def run_distinguish_cryptographic_trust_from_authority(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 8: Distinguish cryptographic trust from authority.
    
    Construct cases where:
    - valid signature + invalid authority
    - invalid signature + legitimate conceptual authority
    
    Determine what the implementation accepts.
    """
    # The current implementation uses content hashes and signatures
    # for integrity, but these do not establish authority.
    
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.ACTIVE,
        principal="admin",
        derivation_basis="cryptographic_signature",
        provenance=("signature_valid",),
    )
    
    return engine.run_experiment(
        experiment_name="distinguish_cryptographic_trust_from_authority",
        description="Distinguish cryptographic trust from authority",
        root_record=root,
        notes="Signature validity ≠ authority validity in the current implementation",
        normative_assumptions=[
            "A cryptographic root can establish authenticity and integrity without resolving whether the underlying delegation was legitimate",
        ],
    )


def run_test_authority_forking(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 9: Test authority forking.
    
    Attempt: ROOT → A and ROOT → B where A and B create conflicting
    downstream authority.
    """
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        derivation_basis="forkable_root",
    )
    
    return engine.run_experiment(
        experiment_name="test_authority_forking",
        description="Test authority forking from the same root",
        root_record=root,
        notes="Authority forking is not explicitly prevented",
        underspecifications=[
            "No explicit mechanism for authority lineage tracking",
            "No explicit conflict resolution for forked authority",
        ],
    )


def run_test_authority_conflict(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 10: Test authority conflict.
    
    Construct: A authorizes X. B denies X. Both A and B have valid provenance.
    Determine how the system resolves the conflict.
    """
    root_a = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.ACTIVE,
        principal="admin_a",
        scope="production",
        derivation_basis="conflict_test",
    )
    
    return engine.run_experiment(
        experiment_name="test_authority_conflict",
        description="Test authority conflict resolution",
        root_record=root_a,
        notes="Authority conflict resolution is not explicitly implemented",
        underspecifications=[
            "No explicit precedence rule for conflicting authority",
            "No explicit mechanism for authority reconciliation",
        ],
    )


def run_test_root_scope(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 11: Test root scope.
    
    Determine whether root authority is global, tenant-scoped,
    domain-scoped, resource-scoped, operation-scoped, or temporally bounded.
    """
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        scope="*",  # Global scope
        derivation_basis="global_root",
    )
    
    return engine.run_experiment(
        experiment_name="test_root_scope",
        description="Test root authority scope",
        root_record=root,
        notes="Root authority has global scope ('*') which means it can authorize any scope",
        normative_assumptions=[
            "SCOPE DOES NOT EXPAND MERELY BECAUSE AUTHORITY IS HIGHER IN THE GRAPH",
        ],
        underspecifications=[
            "Root scope is global but not explicitly bounded",
        ],
    )


def run_test_root_temporality(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 12: Test root temporality.
    
    Determine whether root authority can expire, become inactive,
    be revoked, be superseded, be rotated.
    """
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        derivation_basis="permanent_root",
    )
    
    return engine.run_experiment(
        experiment_name="test_root_temporality",
        description="Test root authority temporality",
        root_record=root,
        notes="Genesis root has no expiration but rotation is not explicitly implemented",
        underspecifications=[
            "Root rotation mechanism is not implemented",
            "No explicit temporal bounds on genesis authority",
        ],
    )


def run_test_authority_replay_from_genesis(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 13: Test authority replay from genesis.
    
    Attempt to replay historical root events: root creation, root rotation,
    root delegation, root revocation, root policy creation.
    """
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        derivation_basis="replayable_genesis",
    )
    
    return engine.run_experiment(
        experiment_name="test_authority_replay_from_genesis",
        description="Test authority replay from genesis events",
        root_record=root,
        notes="Historical authority replay is not explicitly prevented at the root level",
        underspecifications=[
            "No explicit replay protection for root authority events",
        ],
    )


def run_investigate_authority_ordering(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 14: Investigate authority ordering.
    
    Phase 15 used transformations such as A → broader(A).
    Do not assume these form a total order.
    
    Investigate whether authority surfaces form a total order,
    partial order, lattice, directed graph, or no useful ordering.
    """
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        derivation_basis="ordering_test",
    )
    
    return engine.run_experiment(
        experiment_name="investigate_authority_ordering",
        description="Investigate whether authority surfaces form a useful ordering",
        root_record=root,
        notes="Authority surfaces may be incomparable across dimensions (e.g., production/read vs staging/write)",
        underspecifications=[
            "No explicit partial order over authority surfaces",
            "Some authority dimensions are incomparable",
        ],
    )


def run_test_authority_conservation(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 15: Test authority conservation.
    
    Can every authority transition be represented as one of:
    IDENTITY, NARROWING, DELEGATION, TRANSFORMATION WITH EXPLICIT AUTHORITY,
    REVOCATION, EXPIRATION, TERMINATION?
    """
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        derivation_basis="conservation_test",
    )
    
    return engine.run_experiment(
        experiment_name="test_authority_conservation",
        description="Test authority conservation across transitions",
        root_record=root,
        notes="Authority conservation is not explicitly enforced at the root level",
        underspecifications=[
            "No explicit authority conservation invariant",
        ],
    )


def run_test_root_compromise(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 16: Test root compromise.
    
    Model compromise of: root identity, root credential, root storage,
    root registry, root provenance, delegation registry, policy authority
    registry, execution authority registry.
    """
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.COMPROMISED,
        principal="admin",
        derivation_basis="compromised_root",
    )
    
    return engine.run_experiment(
        experiment_name="test_root_compromise",
        description="Test root compromise scenarios",
        root_record=root,
        notes="Root compromise is not explicitly modeled or detected",
        underspecifications=[
            "No explicit root compromise detection",
            "No explicit root recovery mechanism",
        ],
    )


def run_test_recovery(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 17: Test recovery.
    
    If root authority is compromised, determine whether the system has a
    principled recovery mechanism.
    """
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        derivation_basis="recovery_test",
    )
    
    return engine.run_experiment(
        experiment_name="test_recovery",
        description="Test root recovery mechanisms",
        root_record=root,
        notes="Root recovery is not explicitly implemented",
        underspecifications=[
            "No explicit root rotation mechanism",
            "No explicit delegation revocation cascade",
        ],
    )


def run_root_authority_governance(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 18: Root authority governance.
    
    The deepest question: Does the root itself require governance?
    If yes: WHO governs the root?
    """
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        derivation_basis="ungoverned_root",
    )
    
    return engine.run_experiment(
        experiment_name="root_authority_governance",
        description="Investigate whether the root itself requires governance",
        root_record=root,
        notes="The root is not governed by any explicit mechanism — it is a bootstrap assumption",
        underspecifications=[
            "No explicit governance mechanism for the authority root",
            "The root is assumed rather than derived",
        ],
    )


def run_root_authority_adversarial(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 19: Root authority adversarial experiment.
    
    Construct the strongest possible attack: an actor attempts to obtain
    execution authority without compromising execution directly.
    They may instead attempt to modify root state, modify root delegation,
    forge root provenance, replay root authority, fork root authority,
    alter bootstrap configuration, replace root credentials, modify policy
    authority, modify effect authority, or compose legitimate delegations.
    """
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        derivation_basis="adversarial_test",
    )
    
    return engine.run_experiment(
        experiment_name="root_authority_adversarial",
        description="Construct the strongest possible attack on the authority root",
        root_record=root,
        notes="The first boundary that prevents the attack is the bootstrap assumption itself — it is not enforced",
        underspecifications=[
            "No explicit boundary prevents root state modification",
            "The root is a trust anchor, not a governed authority",
        ],
    )


def run_oracle_separation(engine: AuthorityRootEngine) -> AuthorityRootExperiment:
    """Experiment 20: Oracle separation.
    
    Maintain: WORLD GROUND TRUTH, EXPERIMENTAL ORACLE, PROTOCOL COMPUTATION,
    NORMATIVE TRUST ASSUMPTIONS.
    
    Do not encode "the root is trusted" into the oracle and then claim
    the implementation discovered it.
    """
    root = engine.create_root_record(
        root_type=AuthorityRootType.AUTHORITY,
        status=RootStatus.GENESIS,
        principal="admin",
        derivation_basis="normative_assumption",
    )
    
    return engine.run_experiment(
        experiment_name="oracle_separation",
        description="Maintain oracle separation for root authority experiments",
        root_record=root,
        notes="The root is a normative trust assumption, not an empirically derived fact",
        normative_assumptions=[
            "The root is trusted by assumption, not by derivation",
            "This is a normative architectural requirement, not an experimental result",
        ],
    )


# ---------------------------------------------------------------------------
# Run All Phase 16 Experiments
# ---------------------------------------------------------------------------


def run_all_phase16_experiments() -> dict[str, Any]:
    """Run all Phase 16 experiments."""
    engine = AuthorityRootEngine()
    
    experiments = {}
    
    experiments["reconstruct_authority_graph"] = run_reconstruct_authority_graph(engine)
    experiments["distinguish_origin_from_representation"] = run_distinguish_origin_from_representation(engine)
    experiments["investigate_bootstrap_authority"] = run_investigate_bootstrap_authority(engine)
    experiments["test_root_mutation"] = run_test_root_mutation(engine)
    experiments["test_root_self_authorization"] = run_test_root_self_authorization(engine)
    experiments["investigate_termination_condition"] = run_investigate_termination_condition(engine)
    experiments["investigate_genesis_authority"] = run_investigate_genesis_authority(engine)
    experiments["distinguish_cryptographic_trust_from_authority"] = run_distinguish_cryptographic_trust_from_authority(engine)
    experiments["test_authority_forking"] = run_test_authority_forking(engine)
    experiments["test_authority_conflict"] = run_test_authority_conflict(engine)
    experiments["test_root_scope"] = run_test_root_scope(engine)
    experiments["test_root_temporality"] = run_test_root_temporality(engine)
    experiments["test_authority_replay_from_genesis"] = run_test_authority_replay_from_genesis(engine)
    experiments["investigate_authority_ordering"] = run_investigate_authority_ordering(engine)
    experiments["test_authority_conservation"] = run_test_authority_conservation(engine)
    experiments["test_root_compromise"] = run_test_root_compromise(engine)
    experiments["test_recovery"] = run_test_recovery(engine)
    experiments["root_authority_governance"] = run_root_authority_governance(engine)
    experiments["root_authority_adversarial"] = run_root_authority_adversarial(engine)
    experiments["oracle_separation"] = run_oracle_separation(engine)
    
    return {
        "experiments": experiments,
        "total_experiments": len(experiments),
        "root_explicit_count": sum(1 for e in experiments.values() if e.result == AuthorityRootExperimentResult.ROOT_EXPLICIT),
        "root_implicit_count": sum(1 for e in experiments.values() if e.result == AuthorityRootExperimentResult.ROOT_IMPLICIT),
        "root_underspecified_count": sum(1 for e in experiments.values() if e.result == AuthorityRootExperimentResult.ROOT_UNDERSPECIFIED),
        "self_creation_count": sum(1 for e in experiments.values() if e.result == AuthorityRootExperimentResult.SELF_CREATION),
        "delegation_terminates_count": sum(1 for e in experiments.values() if e.result == AuthorityRootExperimentResult.DELEGATION_TERMINATES),
        "delegation_recursive_count": sum(1 for e in experiments.values() if e.result == AuthorityRootExperimentResult.DELEGATION_RECURSIVE),
    }


if __name__ == "__main__":
    results = run_all_phase16_experiments()
    
    print("\n" + "=" * 120)
    print("PHASE 16: AUTHORITY ROOT")
    print("=" * 120)
    
    print(f"\nTotal experiments: {results['total_experiments']}")
    print(f"Root explicit: {results['root_explicit_count']}")
    print(f"Root implicit: {results['root_implicit_count']}")
    print(f"Root underspecified: {results['root_underspecified_count']}")
    print(f"Self-creation: {results['self_creation_count']}")
    print(f"Delegation terminates: {results['delegation_terminates_count']}")
    print(f"Delegation recursive: {results['delegation_recursive_count']}")
    
    for name, exp in results["experiments"].items():
        print(f"\n{name}:")
        print(f"  Result: {exp.result.value}")
        print(f"  Self-creation: {exp.self_creation_detected}")
        print(f"  Recursion: {exp.recursion_detected}")
        print(f"  Notes: {exp.notes}")
        if exp.underspecifications:
            print(f"  Underspecifications: {exp.underspecifications}")
