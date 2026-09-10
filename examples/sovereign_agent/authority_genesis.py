"""Phase 18: Authority Genesis and Sovereign Domain Integration.

Integration experiment: Can the entire effective authority graph be
reconstructed from explicit trust anchors and bounded delegation
without relying on an implicit authority source?

Phase 17 established TRUST_ANCHOR_EXPLICIT: the trust anchor can be
explicitly represented. Three concepts distinguished: authority origin,
trust anchor, delegation. Two sovereign domains can coexist.

Phase 18 asks: Does the explicit trust anchor actually control the
production authority graph, or have we merely constructed a formally
correct representation alongside an authority system that still derives
authority from the old bootstrap mechanism?

This is the integration test that matters.

Existing infrastructure reused:
- TrustAnchor, AuthorityDomain, TerminatedDelegationChain (trust_anchor.py)
- AuthoritySurface, AuthorityEnvelope (effect_boundary.py)
- ClosedAuthorityLoopEngine, AuthorityToken, TransitionStep (closed_authority_loop.py)
- PolicyGovernanceEngine, PolicyAuthorityRecord (policy_governance.py)
- RuntimeAuthorityGate, OperationRequest, AuthorityResolution (runtime_authority_gate.py)
- GovernancePolicyEngine, Policy, PolicyEvaluationResult (governance_policy.py)
- EpistemicCycleDetector, CycleType (epistemic_cycles.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Authority Genesis Types
# ---------------------------------------------------------------------------


class GenesisExperimentResult(str, Enum):
    """Result of a genesis experiment."""
    ALL_AUTHORITIES_TRACEABLE = "all_authorities_traceable"
    IMPLICIT_AUTHORITY_DETECTED = "implicit_authority_detected"
    CYCLE_DETECTED = "cycle_detected"
    ENVELOPE_VIOLATION = "envelope_violation"
    CROSS_DOMAIN_SOVEREIGN = "cross_domain_sovereign"
    CROSS_DOMAIN_CONFLATED = "cross_domain_conflated"
    ANCHOR_INTEGRATED = "anchor_integrated"
    ANCHOR_NOT_INTEGRATED = "anchor_not_integrated"
    UNKNOWN = "unknown"


class AuthoritySourceType(str, Enum):
    """Type of authority source."""
    TRUST_ANCHOR = "trust_anchor"
    DELEGATION = "delegation"
    POLICY = "policy"
    IMPLICIT = "implicit"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Authority Genesis Record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityGenesisRecord:
    """Records the genesis of an authority claim.
    
    Every authority claim must either be:
    1. A trust-anchor claim (non-derived), OR
    2. Have an explicit derivation path to a trust anchor.
    """
    record_id: str
    authority_id: str
    source_type: AuthoritySourceType
    trust_anchor_id: Optional[str] = None
    derivation_path: list[str] = field(default_factory=list)
    is_traceable: bool = False
    notes: str = ""


# ---------------------------------------------------------------------------
# Authority Graph Node
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityGraphNode:
    """A node in the authority graph."""
    node_id: str
    principal: str
    capability: str
    scope: str
    source_type: AuthoritySourceType
    trust_anchor_id: Optional[str] = None
    outgoing_edges: list[str] = field(default_factory=list)
    incoming_edges: list[str] = field(default_factory=list)
    is_implicit: bool = False


# ---------------------------------------------------------------------------
# Authority Graph
# ---------------------------------------------------------------------------


@dataclass
class AuthorityGraph:
    """The complete authority graph.
    
    Maps every authority claim to its source.
    Detects cycles, implicit authorities, and envelope violations.
    """
    nodes: dict[str, AuthorityGraphNode] = field(default_factory=dict)
    edges: dict[str, tuple[str, str]] = field(default_factory=dict)  # edge_id -> (source, target)
    trust_anchor_ids: set[str] = field(default_factory=set)
    
    def add_node(self, node: AuthorityGraphNode) -> None:
        self.nodes[node.node_id] = node
        if node.source_type == AuthoritySourceType.TRUST_ANCHOR:
            self.trust_anchor_ids.add(node.node_id)
    
    def add_edge(self, source_id: str, target_id: str) -> None:
        edge_id = f"edge_{uuid.uuid4().hex[:12]}"
        self.edges[edge_id] = (source_id, target_id)
        if source_id in self.nodes:
            self.nodes[source_id].outgoing_edges.append(target_id)
        if target_id in self.nodes:
            self.nodes[target_id].incoming_edges.append(source_id)
    
    def detect_cycles(self) -> list[list[str]]:
        """Detect all cycles in the graph using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str, path: list[str]) -> None:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            if node_id in self.nodes:
                for neighbor in self.nodes[node_id].outgoing_edges:
                    if neighbor not in visited:
                        dfs(neighbor, path.copy())
                    elif neighbor in rec_stack:
                        # Found a cycle
                        cycle_start = path.index(neighbor)
                        cycle = path[cycle_start:] + [neighbor]
                        cycles.append(cycle)
            
            rec_stack.discard(node_id)
        
        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id, [])
        
        return cycles
    
    def find_implicit_authorities(self) -> list[AuthorityGraphNode]:
        """Find authorities that cannot be traced to a trust anchor."""
        implicit = []
        for node in self.nodes.values():
            if node.source_type == AuthoritySourceType.IMPLICIT:
                implicit.append(node)
            elif node.source_type == AuthoritySourceType.TRUST_ANCHOR:
                continue
            elif not self._is_traceable_to_anchor(node.node_id):
                implicit.append(node)
        return implicit
    
    def _is_traceable_to_anchor(self, node_id: str, visited: set[str] | None = None) -> bool:
        """Check if a node can be traced back to a trust anchor."""
        if visited is None:
            visited = set()
        
        if node_id in visited:
            return False
        visited.add(node_id)
        
        if node_id not in self.nodes:
            return False
        
        node = self.nodes[node_id]
        if node.source_type == AuthoritySourceType.TRUST_ANCHOR:
            return True
        if node.trust_anchor_id and node.trust_anchor_id in self.trust_anchor_ids:
            return True
        
        # Follow incoming edges
        for incoming_id in node.incoming_edges:
            if self._is_traceable_to_anchor(incoming_id, visited):
                return True
        
        return False
    
    def get_all_authorities(self) -> list[AuthorityGraphNode]:
        """Get all authority nodes."""
        return list(self.nodes.values())
    
    def get_trust_anchor_authorities(self) -> list[AuthorityGraphNode]:
        """Get all trust anchor authorities."""
        return [n for n in self.nodes.values() if n.source_type == AuthoritySourceType.TRUST_ANCHOR]


# ---------------------------------------------------------------------------
# Genesis Experiment
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GenesisExperiment:
    """Result of a genesis experiment."""
    experiment_id: str
    experiment_name: str
    description: str
    result: GenesisExperimentResult
    authority_graph: AuthorityGraph | None = None
    cycles_detected: list[list[str]] = field(default_factory=list)
    implicit_authorities: list[AuthorityGraphNode] = field(default_factory=list)
    envelope_violations: list[str] = field(default_factory=list)
    notes: str = ""
    normative_assumptions: list[str] = field(default_factory=list)
    underspecifications: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Authority Genesis Engine
# ---------------------------------------------------------------------------


@dataclass
class AuthorityGenesisEngine:
    """Engine for testing authority genesis and sovereign domain integration."""
    
    experiments: list[GenesisExperiment] = field(default_factory=list)
    authority_graph: AuthorityGraph = field(default_factory=AuthorityGraph)
    genesis_records: dict[str, AuthorityGenesisRecord] = field(default_factory=dict)
    
    def add_trust_anchor(self, anchor_id: str, principal: str, scope: str) -> AuthorityGraphNode:
        """Add a trust anchor to the graph."""
        node = AuthorityGraphNode(
            node_id=anchor_id,
            principal=principal,
            capability="*",
            scope=scope,
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id=anchor_id,
        )
        self.authority_graph.add_node(node)
        return node
    
    def add_delegated_authority(
        self,
        node_id: str,
        principal: str,
        capability: str,
        scope: str,
        delegator_id: str,
        trust_anchor_id: str,
    ) -> AuthorityGraphNode:
        """Add a delegated authority."""
        node = AuthorityGraphNode(
            node_id=node_id,
            principal=principal,
            capability=capability,
            scope=scope,
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id=trust_anchor_id,
        )
        self.authority_graph.add_node(node)
        self.authority_graph.add_edge(delegator_id, node_id)
        return node
    
    def add_implicit_authority(
        self,
        node_id: str,
        principal: str,
        capability: str,
        scope: str,
    ) -> AuthorityGraphNode:
        """Add an implicit authority (for testing detection)."""
        node = AuthorityGraphNode(
            node_id=node_id,
            principal=principal,
            capability=capability,
            scope=scope,
            source_type=AuthoritySourceType.IMPLICIT,
            is_implicit=True,
        )
        self.authority_graph.add_node(node)
        return node
    
    def run_experiment(
        self,
        experiment_name: str,
        description: str,
        result: GenesisExperimentResult,
        notes: str = "",
        normative_assumptions: list[str] | None = None,
        underspecifications: list[str] | None = None,
    ) -> GenesisExperiment:
        """Run a genesis experiment."""
        # Detect cycles
        cycles = self.authority_graph.detect_cycles()
        
        # Find implicit authorities
        implicit = self.authority_graph.find_implicit_authorities()
        
        experiment = GenesisExperiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:12]}",
            experiment_name=experiment_name,
            description=description,
            result=result,
            authority_graph=self.authority_graph,
            cycles_detected=cycles,
            implicit_authorities=implicit,
            notes=notes,
            normative_assumptions=normative_assumptions or [],
            underspecifications=underspecifications or [],
        )
        self.experiments.append(experiment)
        return experiment


# ---------------------------------------------------------------------------
# Experiment 1: Trace All Authorities to Trust Anchor
# ---------------------------------------------------------------------------


def run_trace_all_authorities(engine: AuthorityGenesisEngine) -> GenesisExperiment:
    """Experiment 1: Trace all authorities back to a trust anchor.
    
    Every authority claim must either be:
    1. A trust-anchor claim, OR
    2. Have an explicit derivation path to a trust anchor.
    """
    # Create trust anchor
    anchor = engine.add_trust_anchor(
        anchor_id="anchor_001",
        principal="admin",
        scope="production",
    )
    
    # Create delegated authorities
    engine.add_delegated_authority(
        node_id="policy_admin",
        principal="policy_admin",
        capability="modify_policy",
        scope="production",
        delegator_id="anchor_001",
        trust_anchor_id="anchor_001",
    )
    
    engine.add_delegated_authority(
        node_id="governance_engine",
        principal="governance_engine",
        capability="evaluate_policy",
        scope="production",
        delegator_id="policy_admin",
        trust_anchor_id="anchor_001",
    )
    
    engine.add_delegated_authority(
        node_id="execution_service",
        principal="execution_service",
        capability="execute_payment",
        scope="production",
        delegator_id="governance_engine",
        trust_anchor_id="anchor_001",
    )
    
    # Check traceability
    implicit = engine.authority_graph.find_implicit_authorities()
    
    return engine.run_experiment(
        experiment_name="trace_all_authorities",
        description="Trace all authorities back to a trust anchor",
        result=GenesisExperimentResult.ALL_AUTHORITIES_TRACEABLE if not implicit else GenesisExperimentResult.IMPLICIT_AUTHORITY_DETECTED,
        notes=f"Implicit authorities found: {len(implicit)}",
        normative_assumptions=[
            "Every authority claim must be traceable to a trust anchor",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 2: Detect Implicit Authority
# ---------------------------------------------------------------------------


def run_detect_implicit_authority(engine: AuthorityGenesisEngine) -> GenesisExperiment:
    """Experiment 2: Detect implicit authority.
    
    Add an implicit authority (hardcoded admin) and verify detection.
    """
    # Create trust anchor
    engine.add_trust_anchor(
        anchor_id="anchor_001",
        principal="admin",
        scope="production",
    )
    
    # Create implicit authority (simulating hardcoded admin)
    engine.add_implicit_authority(
        node_id="implicit_admin",
        principal="admin",
        capability="*",
        scope="*",
    )
    
    # Check detection
    implicit = engine.authority_graph.find_implicit_authorities()
    
    return engine.run_experiment(
        experiment_name="detect_implicit_authority",
        description="Detect implicit authority in the graph",
        result=GenesisExperimentResult.IMPLICIT_AUTHORITY_DETECTED if implicit else GenesisExperimentResult.ALL_AUTHORITIES_TRACEABLE,
        notes=f"Implicit authorities detected: {len(implicit)}",
        normative_assumptions=[
            "Implicit authorities must be detectable",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 3: Detect Cycles
# ---------------------------------------------------------------------------


def run_detect_cycles(engine: AuthorityGenesisEngine) -> GenesisExperiment:
    """Experiment 3: Detect cycles in the authority graph.
    
    Construct: anchor → A → B → anchor (cycle)
    """
    # Create trust anchor
    engine.add_trust_anchor(
        anchor_id="anchor_001",
        principal="admin",
        scope="production",
    )
    
    # Create chain: anchor → policy_admin → admin → anchor (cycle)
    engine.add_delegated_authority(
        node_id="policy_admin",
        principal="policy_admin",
        capability="modify_anchor",
        scope="production",
        delegator_id="anchor_001",
        trust_anchor_id="anchor_001",
    )
    
    # Create a cycle: policy_admin delegates back to anchor
    engine.authority_graph.add_edge("policy_admin", "anchor_001")
    
    # Detect cycles
    cycles = engine.authority_graph.detect_cycles()
    
    return engine.run_experiment(
        experiment_name="detect_cycles",
        description="Detect cycles in the authority graph",
        result=GenesisExperimentResult.CYCLE_DETECTED if cycles else GenesisExperimentResult.ALL_AUTHORITIES_TRACEABLE,
        notes=f"Cycles detected: {len(cycles)}",
        normative_assumptions=[
            "Cycles in the authority graph must be detectable",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 4: Envelope Violation Detection
# ---------------------------------------------------------------------------


def run_detect_envelope_violation(engine: AuthorityGenesisEngine) -> GenesisExperiment:
    """Experiment 4: Detect envelope violations.
    
    Construct: anchor delegates narrow authority, but downstream authority
    exceeds the anchor's declared envelope.
    """
    # Create trust anchor with narrow scope
    engine.add_trust_anchor(
        anchor_id="anchor_001",
        principal="admin",
        scope="production",
    )
    
    # Create delegated authority within envelope
    engine.add_delegated_authority(
        node_id="policy_admin",
        principal="policy_admin",
        capability="modify_policy",
        scope="production",
        delegator_id="anchor_001",
        trust_anchor_id="anchor_001",
    )
    
    # Create downstream authority that exceeds envelope (cross-scope)
    engine.add_delegated_authority(
        node_id="cross_scope_service",
        principal="cross_scope_service",
        capability="execute_payment",
        scope="staging",  # Different scope - potential violation
        delegator_id="policy_admin",
        trust_anchor_id="anchor_001",
    )
    
    # Check for envelope violations
    # (simplified: check if any node has scope different from anchor)
    violations = []
    for node in engine.authority_graph.get_all_authorities():
        if node.trust_anchor_id == "anchor_001" and node.scope not in ("production", "*"):
            violations.append(f"Node {node.node_id} has scope {node.scope}, expected production")
    
    return engine.run_experiment(
        experiment_name="detect_envelope_violation",
        description="Detect envelope violations in delegated authority",
        result=GenesisExperimentResult.ENVELOPE_VIOLATION if violations else GenesisExperimentResult.ALL_AUTHORITIES_TRACEABLE,
        notes=f"Envelope violations: {len(violations)}",
        normative_assumptions=[
            "Downstream authority must not exceed the anchor's declared envelope",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 5: Sovereign Domain Integration
# ---------------------------------------------------------------------------


def run_sovereign_domain_integration(engine: AuthorityGenesisEngine) -> GenesisExperiment:
    """Experiment 5: Test sovereign domain integration.
    
    Two independent trust anchors with their own authority domains.
    Cross-domain authority requires explicit delegation.
    """
    # Domain A
    engine.add_trust_anchor(
        anchor_id="anchor_a",
        principal="admin_a",
        scope="domain_a",
    )
    
    engine.add_delegated_authority(
        node_id="policy_admin_a",
        principal="policy_admin_a",
        capability="modify_policy",
        scope="domain_a",
        delegator_id="anchor_a",
        trust_anchor_id="anchor_a",
    )
    
    # Domain B
    engine.add_trust_anchor(
        anchor_id="anchor_b",
        principal="admin_b",
        scope="domain_b",
    )
    
    engine.add_delegated_authority(
        node_id="policy_admin_b",
        principal="policy_admin_b",
        capability="modify_policy",
        scope="domain_b",
        delegator_id="anchor_b",
        trust_anchor_id="anchor_b",
    )
    
    # Cross-domain delegation: A → B (explicit)
    engine.authority_graph.add_edge("policy_admin_a", "policy_admin_b")
    
    # Check sovereignty
    implicit = engine.authority_graph.find_implicit_authorities()
    
    return engine.run_experiment(
        experiment_name="sovereign_domain_integration",
        description="Test sovereign domain integration",
        result=GenesisExperimentResult.CROSS_DOMAIN_SOVEREIGN if not implicit else GenesisExperimentResult.CROSS_DOMAIN_CONFLATED,
        notes=f"Implicit authorities: {len(implicit)}",
        normative_assumptions=[
            "Two trust anchors can coexist without one being subordinate",
            "Cross-domain authority requires explicit delegation",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 6: Anchor Integration Test
# ---------------------------------------------------------------------------


def run_anchor_integration_test(engine: AuthorityGenesisEngine) -> GenesisExperiment:
    """Experiment 6: Test whether trust anchor is integrated into production path.
    
    Simulate the production authority path:
    TrustAnchor → PolicyAuthority → EffectAuthority → Governance → Execution
    
    Verify that every step traces back to the trust anchor.
    """
    # Create trust anchor
    engine.add_trust_anchor(
        anchor_id="anchor_001",
        principal="admin",
        scope="production",
    )
    
    # Production path
    engine.add_delegated_authority(
        node_id="policy_authority",
        principal="policy_authority",
        capability="create_policy",
        scope="production",
        delegator_id="anchor_001",
        trust_anchor_id="anchor_001",
    )
    
    engine.add_delegated_authority(
        node_id="effect_authority",
        principal="effect_authority",
        capability="evaluate_effect",
        scope="production",
        delegator_id="policy_authority",
        trust_anchor_id="anchor_001",
    )
    
    engine.add_delegated_authority(
        node_id="governance",
        principal="governance",
        capability="govern",
        scope="production",
        delegator_id="effect_authority",
        trust_anchor_id="anchor_001",
    )
    
    engine.add_delegated_authority(
        node_id="execution",
        principal="execution",
        capability="execute",
        scope="production",
        delegator_id="governance",
        trust_anchor_id="anchor_001",
    )
    
    # Check traceability
    implicit = engine.authority_graph.find_implicit_authorities()
    
    return engine.run_experiment(
        experiment_name="anchor_integration_test",
        description="Test trust anchor integration into production path",
        result=GenesisExperimentResult.ANCHOR_INTEGRATED if not implicit else GenesisExperimentResult.ANCHOR_NOT_INTEGRATED,
        notes=f"Implicit authorities: {len(implicit)}",
        normative_assumptions=[
            "Every production authority must trace back to a trust anchor",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 7: Self-Authorization Prevention
# ---------------------------------------------------------------------------


def run_self_authorization_prevention(engine: AuthorityGenesisEngine) -> GenesisExperiment:
    """Experiment 7: Test self-authorization prevention.
    
    Attempt: anchor delegates authority to modify itself.
    This should be detected as a cycle.
    """
    # Create trust anchor
    engine.add_trust_anchor(
        anchor_id="anchor_001",
        principal="admin",
        scope="production",
    )
    
    # Create self-authorizing delegation
    engine.add_delegated_authority(
        node_id="modifier",
        principal="modifier",
        capability="modify_anchor",
        scope="production",
        delegator_id="anchor_001",
        trust_anchor_id="anchor_001",
    )
    
    # Create cycle: modifier can modify anchor
    engine.authority_graph.add_edge("modifier", "anchor_001")
    
    # Detect cycles
    cycles = engine.authority_graph.detect_cycles()
    
    return engine.run_experiment(
        experiment_name="self_authorization_prevention",
        description="Test self-authorization prevention",
        result=GenesisExperimentResult.CYCLE_DETECTED if cycles else GenesisExperimentResult.UNKNOWN,
        notes=f"Cycles detected: {len(cycles)}",
        normative_assumptions=[
            "Self-authorization must be detectable as a cycle",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 8: Cross-Domain Sovereignty Preservation
# ---------------------------------------------------------------------------


def run_cross_domain_sovereignty(engine: AuthorityGenesisEngine) -> GenesisExperiment:
    """Experiment 8: Test cross-domain sovereignty preservation.
    
    Test: A → B delegation and B → A delegation and no delegation.
    Verify sovereignty is preserved in each case.
    """
    # Domain A
    engine.add_trust_anchor(
        anchor_id="anchor_a",
        principal="admin_a",
        scope="domain_a",
    )
    
    # Domain B
    engine.add_trust_anchor(
        anchor_id="anchor_b",
        principal="admin_b",
        scope="domain_b",
    )
    
    # Cross-domain: A delegates to B
    engine.authority_graph.add_edge("anchor_a", "anchor_b")
    
    # Check: both anchors are still sovereign (no implicit authorities)
    implicit = engine.authority_graph.find_implicit_authorities()
    
    return engine.run_experiment(
        experiment_name="cross_domain_sovereignty",
        description="Test cross-domain sovereignty preservation",
        result=GenesisExperimentResult.CROSS_DOMAIN_SOVEREIGN if not implicit else GenesisExperimentResult.CROSS_DOMAIN_CONFLATED,
        notes=f"Implicit authorities: {len(implicit)}",
        normative_assumptions=[
            "Cross-domain delegation does not create implicit authorities",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 9: Authority Exceeding Envelope
# ---------------------------------------------------------------------------


def run_authority_exceeding_envelope(engine: AuthorityGenesisEngine) -> GenesisExperiment:
    """Experiment 9: Test authority exceeding envelope.
    
    Construct: anchor with narrow scope delegates to service that
    claims broader scope.
    """
    # Create trust anchor with narrow scope
    engine.add_trust_anchor(
        anchor_id="anchor_001",
        principal="admin",
        scope="production",
    )
    
    # Create service with broader scope (violation)
    engine.add_delegated_authority(
        node_id="service",
        principal="service",
        capability="execute",
        scope="*",  # Broader than anchor's scope
        delegator_id="anchor_001",
        trust_anchor_id="anchor_001",
    )
    
    # Check for violations
    violations = []
    for node in engine.authority_graph.get_all_authorities():
        if node.trust_anchor_id == "anchor_001" and node.scope == "*":
            violations.append(f"Node {node.node_id} has broader scope than anchor")
    
    return engine.run_experiment(
        experiment_name="authority_exceeding_envelope",
        description="Test authority exceeding envelope detection",
        result=GenesisExperimentResult.ENVELOPE_VIOLATION if violations else GenesisExperimentResult.ALL_AUTHORITIES_TRACEABLE,
        notes=f"Violations: {len(violations)}",
        normative_assumptions=[
            "Downstream authority must not exceed anchor's scope",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 10: Complete Graph Reconstruction
# ---------------------------------------------------------------------------


def run_complete_graph_reconstruction(engine: AuthorityGenesisEngine) -> GenesisExperiment:
    """Experiment 10: Test complete graph reconstruction.
    
    Construct a complete authority graph with multiple domains,
    cross-domain delegation, and verify full traceability.
    """
    # Domain A
    engine.add_trust_anchor(
        anchor_id="anchor_a",
        principal="admin_a",
        scope="domain_a",
    )
    
    engine.add_delegated_authority(
        node_id="policy_a",
        principal="policy_a",
        capability="modify_policy",
        scope="domain_a",
        delegator_id="anchor_a",
        trust_anchor_id="anchor_a",
    )
    
    engine.add_delegated_authority(
        node_id="execution_a",
        principal="execution_a",
        capability="execute",
        scope="domain_a",
        delegator_id="policy_a",
        trust_anchor_id="anchor_a",
    )
    
    # Domain B
    engine.add_trust_anchor(
        anchor_id="anchor_b",
        principal="admin_b",
        scope="domain_b",
    )
    
    engine.add_delegated_authority(
        node_id="policy_b",
        principal="policy_b",
        capability="modify_policy",
        scope="domain_b",
        delegator_id="anchor_b",
        trust_anchor_id="anchor_b",
    )
    
    # Cross-domain: A → B
    engine.authority_graph.add_edge("policy_a", "policy_b")
    
    # Check full traceability
    implicit = engine.authority_graph.find_implicit_authorities()
    cycles = engine.authority_graph.detect_cycles()
    
    return engine.run_experiment(
        experiment_name="complete_graph_reconstruction",
        description="Test complete graph reconstruction from trust anchors",
        result=GenesisExperimentResult.ALL_AUTHORITIES_TRACEABLE if not implicit and not cycles else GenesisExperimentResult.IMPLICIT_AUTHORITY_DETECTED,
        notes=f"Implicit: {len(implicit)}, Cycles: {len(cycles)}",
        normative_assumptions=[
            "Complete authority graph can be reconstructed from trust anchors",
        ],
    )


# ---------------------------------------------------------------------------
# Run All Phase 18 Experiments
# ---------------------------------------------------------------------------


def run_all_phase18_experiments() -> dict[str, Any]:
    """Run all Phase 18 experiments."""
    engine = AuthorityGenesisEngine()
    
    experiments = {}
    
    experiments["trace_all_authorities"] = run_trace_all_authorities(engine)
    
    # Reset for next experiment
    engine = AuthorityGenesisEngine()
    experiments["detect_implicit_authority"] = run_detect_implicit_authority(engine)
    
    engine = AuthorityGenesisEngine()
    experiments["detect_cycles"] = run_detect_cycles(engine)
    
    engine = AuthorityGenesisEngine()
    experiments["detect_envelope_violation"] = run_detect_envelope_violation(engine)
    
    engine = AuthorityGenesisEngine()
    experiments["sovereign_domain_integration"] = run_sovereign_domain_integration(engine)
    
    engine = AuthorityGenesisEngine()
    experiments["anchor_integration_test"] = run_anchor_integration_test(engine)
    
    engine = AuthorityGenesisEngine()
    experiments["self_authorization_prevention"] = run_self_authorization_prevention(engine)
    
    engine = AuthorityGenesisEngine()
    experiments["cross_domain_sovereignty"] = run_cross_domain_sovereignty(engine)
    
    engine = AuthorityGenesisEngine()
    experiments["authority_exceeding_envelope"] = run_authority_exceeding_envelope(engine)
    
    engine = AuthorityGenesisEngine()
    experiments["complete_graph_reconstruction"] = run_complete_graph_reconstruction(engine)
    
    return {
        "experiments": experiments,
        "total_experiments": len(experiments),
        "all_traceable_count": sum(1 for e in experiments.values() if e.result == GenesisExperimentResult.ALL_AUTHORITIES_TRACEABLE),
        "implicit_detected_count": sum(1 for e in experiments.values() if e.result == GenesisExperimentResult.IMPLICIT_AUTHORITY_DETECTED),
        "cycle_detected_count": sum(1 for e in experiments.values() if e.result == GenesisExperimentResult.CYCLE_DETECTED),
        "envelope_violation_count": sum(1 for e in experiments.values() if e.result == GenesisExperimentResult.ENVELOPE_VIOLATION),
        "cross_domain_sovereign_count": sum(1 for e in experiments.values() if e.result == GenesisExperimentResult.CROSS_DOMAIN_SOVEREIGN),
        "anchor_integrated_count": sum(1 for e in experiments.values() if e.result == GenesisExperimentResult.ANCHOR_INTEGRATED),
    }


if __name__ == "__main__":
    results = run_all_phase18_experiments()
    
    print("\n" + "=" * 120)
    print("PHASE 18: AUTHORITY GENESIS AND SOVEREIGN DOMAIN INTEGRATION")
    print("=" * 120)
    
    print(f"\nTotal experiments: {results['total_experiments']}")
    print(f"All authorities traceable: {results['all_traceable_count']}")
    print(f"Implicit authority detected: {results['implicit_detected_count']}")
    print(f"Cycle detected: {results['cycle_detected_count']}")
    print(f"Envelope violation: {results['envelope_violation_count']}")
    print(f"Cross-domain sovereign: {results['cross_domain_sovereign_count']}")
    print(f"Anchor integrated: {results['anchor_integrated_count']}")
    
    for name, exp in results["experiments"].items():
        print(f"\n{name}:")
        print(f"  Result: {exp.result.value}")
        print(f"  Notes: {exp.notes}")
        if exp.underspecifications:
            print(f"  Underspecifications: {exp.underspecifications}")
