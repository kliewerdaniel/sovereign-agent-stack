"""Phase 19: Authority Graph Completeness.

Investigates whether the declared authority graph captures all authority
that exists in the system, or whether authority can exist outside the
graph's observation boundary.

Phase 18 established AUTHORITY_GRAPH_RECONSTRUCTIBLE: every authority
claim can be traced back to a declared trust anchor. The graph is
internally consistent.

Phase 19 asks a harder question:

    CAN THE AUTHORITY GRAPH ITSELF BE TRUSTED TO REPRESENT ALL AUTHORITY?

This is the completeness question applied to authority itself.

Critical distinction:
    AUTHORITY_GRAPH_RECONSTRUCTIBLE ≠ AUTHORITY_GRAPH_COMPLETE

A graph can be internally perfect while omitting an authority mechanism
that exists outside the graph. Your earlier dependency completeness work
established this exact principle for dependency graphs. Phase 19
establishes the analogous principle for authority graphs.

The completeness checker MUST NOT become an authority oracle.
    INCOMPLETE → therefore unauthorized  [FORBIDDEN]
    INCOMPLETE → UNKNOWN                  [REQUIRED]

Because you already established that epistemic uncertainty and authority
are separate layers.

Existing infrastructure reused:
- AuthorityGraph, AuthorityGraphNode, AuthoritySourceType (authority_genesis.py)
- TrustAnchor, AuthorityDomain (trust_anchor.py)
- AuthoritySurface, AuthorityEnvelope (effect_boundary.py)
- CompletenessScope, CompletenessStatus, CompletenessDimension (dependency_completeness.py)
- ClosedAuthorityLoopEngine, AuthorityToken (closed_authority_loop.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Authority Graph Completeness Types
# ---------------------------------------------------------------------------


class CompletenessResult(str, Enum):
    """Result of a completeness assessment.
    
    The completeness checker MUST NOT become an authority oracle.
    INCOMPLETE does NOT imply unauthorized.
    COMPLETE does NOT imply authorized.
    UNKNOWN does NOT imply either.
    """
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    UNKNOWN = "unknown"
    FALSE_COMPLETENESS = "false_completeness"
    UNTESTED = "untested"


class CompletenessDimension(str, Enum):
    """Dimensions along which authority graph completeness can be assessed."""
    NODE_COVERAGE = "node_coverage"          # Are all authority nodes captured?
    EDGE_COVERAGE = "edge_coverage"          # Are all delegation edges captured?
    TEMPORAL_COVERAGE = "temporal_coverage"  # Are temporal authorities captured?
    CROSS_DOMAIN_COVERAGE = "cross_domain_coverage"  # Are cross-domain authorities captured?
    FAILURE_PATH_COVERAGE = "failure_path_coverage"  # Are failure-path authorities captured?
    RECOVERY_COVERAGE = "recovery_coverage"  # Are recovery authorities captured?
    EMERGENCY_COVERAGE = "emergency_coverage"  # Are emergency authorities captured?
    OUT_OF_BAND_COVERAGE = "out_of_band_coverage"  # Are out-of-band authorities captured?


class HiddenAuthorityType(str, Enum):
    """Types of authority that can exist outside the declared graph."""
    HIDDEN_NODE = "hidden_node"              # Authority node not in graph
    HIDDEN_EDGE = "hidden_edge"              # Delegation edge not in graph
    HIDDEN_POLICY = "hidden_policy"          # Policy authority not declared
    HIDDEN_CAPABILITY = "hidden_capability"  # Capability escalation not declared
    OUT_OF_BAND_ADMIN = "out_of_band_admin"  # Administrative authority outside protocol
    TEMPORAL_APPEARING = "temporal_appearing"  # Authority that appears only during interval
    FAILURE_PATH = "failure_path"            # Authority activated only on failure
    RECOVERY_PATH = "recovery_path"          # Authority activated only during recovery
    EMERGENCY_OVERRIDE = "emergency_override"  # Emergency authority not in normal graph
    CROSS_DOMAIN_HIDDEN = "cross_domain_hidden"  # Cross-domain authority not declared


# ---------------------------------------------------------------------------
# Authority Graph Completeness Record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompletenessRecord:
    """Records a completeness assessment for an authority graph.
    
    A completeness record is NOT an authority claim. It is an epistemic
    claim about the relationship between the declared graph and the
    actual authority mechanisms in the system.
    """
    record_id: str
    dimension: CompletenessDimension
    result: CompletenessResult
    declared_count: int = 0
    actual_count: int = 0
    hidden_authorities: list[str] = field(default_factory=list)
    missing_edges: list[tuple[str, str]] = field(default_factory=list)
    notes: str = ""
    
    @property
    def is_complete(self) -> bool:
        return self.result == CompletenessResult.COMPLETE
    
    @property
    def is_incomplete(self) -> bool:
        return self.result == CompletenessResult.INCOMPLETE


# ---------------------------------------------------------------------------
# Observable Authority Mechanism
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ObservableAuthorityMechanism:
    """Represents an authority mechanism that exists in the system.
    
    This is the "ground truth" against which the declared graph is compared.
    """
    mechanism_id: str
    mechanism_type: str
    principal: str
    capability: str
    scope: str
    source: str  # Where this authority actually originates
    is_declared: bool = False  # Whether this is in the declared graph
    temporal_interval: tuple[str, str] = ("unbounded", "unbounded")
    activation_condition: str = "always"  # always, on_failure, on_recovery, on_emergency
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Authority Graph Completeness Engine
# ---------------------------------------------------------------------------


@dataclass
class AuthorityGraphCompletenessEngine:
    """Engine for assessing authority graph completeness.
    
    Compares the declared authority graph against the actual observable
    authority mechanisms in the system.
    
    CRITICAL: This engine does NOT authorize anything. It produces
    epistemic claims about graph completeness. INCOMPLETE does NOT
    mean unauthorized.
    """
    
    declared_graph: Any = None  # AuthorityGraph from authority_genesis.py
    observable_mechanisms: list[ObservableAuthorityMechanism] = field(default_factory=list)
    completeness_records: list[CompletenessRecord] = field(default_factory=list)
    hidden_authorities: list[ObservableAuthorityMechanism] = field(default_factory=list)
    
    def add_observable_mechanism(self, mechanism: ObservableAuthorityMechanism) -> None:
        """Add an observable authority mechanism."""
        self.observable_mechanisms.append(mechanism)
        if not mechanism.is_declared:
            self.hidden_authorities.append(mechanism)
    
    def assess_node_coverage(self) -> CompletenessRecord:
        """Assess whether all authority nodes are captured in the declared graph."""
        declared_nodes = {m.mechanism_id for m in self.observable_mechanisms if m.is_declared}
        observable_nodes = {m.mechanism_id for m in self.observable_mechanisms}
        hidden = [m for m in self.observable_mechanisms if not m.is_declared]
        
        result = (
            CompletenessResult.COMPLETE if not hidden
            else CompletenessResult.INCOMPLETE
        )
        
        record = CompletenessRecord(
            record_id=f"record_{uuid.uuid4().hex[:12]}",
            dimension=CompletenessDimension.NODE_COVERAGE,
            result=result,
            declared_count=len(declared_nodes),
            actual_count=len(observable_nodes),
            hidden_authorities=[m.mechanism_id for m in hidden],
            notes=f"Declared: {len(declared_nodes)}, Actual: {len(observable_nodes)}, Hidden: {len(hidden)}",
        )
        self.completeness_records.append(record)
        return record
    
    def assess_edge_coverage(self) -> CompletenessRecord:
        """Assess whether all delegation edges are captured."""
        # An edge is declared if both source and target are declared mechanisms
        declared_mechanisms = {m.mechanism_id for m in self.observable_mechanisms if m.is_declared}
        
        # Build actual edges from observable mechanisms
        actual_edges = set()
        for m in self.observable_mechanisms:
            if m.source != m.mechanism_id:  # Has a source
                actual_edges.add((m.source, m.mechanism_id))
        
        # Declared edges: both source and target are declared
        declared_edges = {
            (src, tgt) for (src, tgt) in actual_edges
            if src in declared_mechanisms and tgt in declared_mechanisms
        }
        
        hidden_edges = actual_edges - declared_edges
        
        result = (
            CompletenessResult.COMPLETE if not hidden_edges
            else CompletenessResult.INCOMPLETE
        )
        
        record = CompletenessRecord(
            record_id=f"record_{uuid.uuid4().hex[:12]}",
            dimension=CompletenessDimension.EDGE_COVERAGE,
            result=result,
            declared_count=len(declared_edges),
            actual_count=len(actual_edges),
            missing_edges=list(hidden_edges),
            notes=f"Declared: {len(declared_edges)}, Actual: {len(actual_edges)}, Hidden: {len(hidden_edges)}",
        )
        self.completeness_records.append(record)
        return record
    
    def assess_temporal_coverage(self) -> CompletenessRecord:
        """Assess whether temporal authorities are captured."""
        temporal_mechanisms = [
            m for m in self.observable_mechanisms
            if m.temporal_interval != ("unbounded", "unbounded")
        ]
        
        # Check if declared graph captures temporal authorities
        declared_temporal = {
            m.mechanism_id for m in self.observable_mechanisms
            if m.is_declared and m.temporal_interval != ("unbounded", "unbounded")
        }
        
        hidden = [
            m for m in temporal_mechanisms
            if m.mechanism_id not in declared_temporal
        ]
        
        result = (
            CompletenessResult.COMPLETE if not hidden
            else CompletenessResult.INCOMPLETE
        )
        
        record = CompletenessRecord(
            record_id=f"record_{uuid.uuid4().hex[:12]}",
            dimension=CompletenessDimension.TEMPORAL_COVERAGE,
            result=result,
            declared_count=len(declared_temporal),
            actual_count=len(temporal_mechanisms),
            hidden_authorities=[m.mechanism_id for m in hidden],
            notes=f"Temporal mechanisms: {len(temporal_mechanisms)}, Hidden: {len(hidden)}",
        )
        self.completeness_records.append(record)
        return record
    
    def assess_cross_domain_coverage(self) -> CompletenessRecord:
        """Assess whether cross-domain authorities are captured."""
        cross_domain = [
            m for m in self.observable_mechanisms
            if m.metadata.get("cross_domain", False)
        ]
        
        declared_cross_domain = {
            m.mechanism_id for m in self.observable_mechanisms
            if m.is_declared and m.metadata.get("cross_domain", False)
        }
        
        hidden = [
            m for m in cross_domain
            if m.mechanism_id not in declared_cross_domain
        ]
        
        result = (
            CompletenessResult.COMPLETE if not hidden
            else CompletenessResult.INCOMPLETE
        )
        
        record = CompletenessRecord(
            record_id=f"record_{uuid.uuid4().hex[:12]}",
            dimension=CompletenessDimension.CROSS_DOMAIN_COVERAGE,
            result=result,
            declared_count=len(declared_cross_domain),
            actual_count=len(cross_domain),
            hidden_authorities=[m.mechanism_id for m in hidden],
            notes=f"Cross-domain: {len(cross_domain)}, Hidden: {len(hidden)}",
        )
        self.completeness_records.append(record)
        return record
    
    def assess_failure_path_coverage(self) -> CompletenessRecord:
        """Assess whether failure-path authorities are captured."""
        failure_path = [
            m for m in self.observable_mechanisms
            if m.activation_condition == "on_failure"
        ]
        
        declared_failure = {
            m.mechanism_id for m in self.observable_mechanisms
            if m.is_declared and m.activation_condition == "on_failure"
        }
        
        hidden = [
            m for m in failure_path
            if m.mechanism_id not in declared_failure
        ]
        
        result = (
            CompletenessResult.COMPLETE if not hidden
            else CompletenessResult.INCOMPLETE
        )
        
        record = CompletenessRecord(
            record_id=f"record_{uuid.uuid4().hex[:12]}",
            dimension=CompletenessDimension.FAILURE_PATH_COVERAGE,
            result=result,
            declared_count=len(declared_failure),
            actual_count=len(failure_path),
            hidden_authorities=[m.mechanism_id for m in hidden],
            notes=f"Failure-path: {len(failure_path)}, Hidden: {len(hidden)}",
        )
        self.completeness_records.append(record)
        return record
    
    def assess_recovery_coverage(self) -> CompletenessRecord:
        """Assess whether recovery authorities are captured."""
        recovery = [
            m for m in self.observable_mechanisms
            if m.activation_condition == "on_recovery"
        ]
        
        declared_recovery = {
            m.mechanism_id for m in self.observable_mechanisms
            if m.is_declared and m.activation_condition == "on_recovery"
        }
        
        hidden = [
            m for m in recovery
            if m.mechanism_id not in declared_recovery
        ]
        
        result = (
            CompletenessResult.COMPLETE if not hidden
            else CompletenessResult.INCOMPLETE
        )
        
        record = CompletenessRecord(
            record_id=f"record_{uuid.uuid4().hex[:12]}",
            dimension=CompletenessDimension.RECOVERY_COVERAGE,
            result=result,
            declared_count=len(declared_recovery),
            actual_count=len(recovery),
            hidden_authorities=[m.mechanism_id for m in hidden],
            notes=f"Recovery: {len(recovery)}, Hidden: {len(hidden)}",
        )
        self.completeness_records.append(record)
        return record
    
    def assess_emergency_coverage(self) -> CompletenessRecord:
        """Assess whether emergency authorities are captured."""
        emergency = [
            m for m in self.observable_mechanisms
            if m.activation_condition == "on_emergency"
        ]
        
        declared_emergency = {
            m.mechanism_id for m in self.observable_mechanisms
            if m.is_declared and m.activation_condition == "on_emergency"
        }
        
        hidden = [
            m for m in emergency
            if m.mechanism_id not in declared_emergency
        ]
        
        result = (
            CompletenessResult.COMPLETE if not hidden
            else CompletenessResult.INCOMPLETE
        )
        
        record = CompletenessRecord(
            record_id=f"record_{uuid.uuid4().hex[:12]}",
            dimension=CompletenessDimension.EMERGENCY_COVERAGE,
            result=result,
            declared_count=len(declared_emergency),
            actual_count=len(emergency),
            hidden_authorities=[m.mechanism_id for m in hidden],
            notes=f"Emergency: {len(emergency)}, Hidden: {len(hidden)}",
        )
        self.completeness_records.append(record)
        return record
    
    def assess_out_of_band_coverage(self) -> CompletenessRecord:
        """Assess whether out-of-band authorities are captured."""
        out_of_band = [
            m for m in self.observable_mechanisms
            if m.metadata.get("out_of_band", False)
        ]
        
        declared_oob = {
            m.mechanism_id for m in self.observable_mechanisms
            if m.is_declared and m.metadata.get("out_of_band", False)
        }
        
        hidden = [
            m for m in out_of_band
            if m.mechanism_id not in declared_oob
        ]
        
        result = (
            CompletenessResult.COMPLETE if not hidden
            else CompletenessResult.INCOMPLETE
        )
        
        record = CompletenessRecord(
            record_id=f"record_{uuid.uuid4().hex[:12]}",
            dimension=CompletenessDimension.OUT_OF_BAND_COVERAGE,
            result=result,
            declared_count=len(declared_oob),
            actual_count=len(out_of_band),
            hidden_authorities=[m.mechanism_id for m in hidden],
            notes=f"Out-of-band: {len(out_of_band)}, Hidden: {len(hidden)}",
        )
        self.completeness_records.append(record)
        return record
    
    def assess_all_dimensions(self) -> list[CompletenessRecord]:
        """Run all completeness assessments."""
        return [
            self.assess_node_coverage(),
            self.assess_edge_coverage(),
            self.assess_temporal_coverage(),
            self.assess_cross_domain_coverage(),
            self.assess_failure_path_coverage(),
            self.assess_recovery_coverage(),
            self.assess_emergency_coverage(),
            self.assess_out_of_band_coverage(),
        ]
    
    def get_overall_completeness(self) -> CompletenessResult:
        """Get overall completeness across all dimensions.
        
        Returns:
            COMPLETE if all dimensions are complete
            INCOMPLETE if any dimension is incomplete
            UNKNOWN if no assessments have been run
        """
        if not self.completeness_records:
            return CompletenessResult.UNKNOWN
        
        if all(r.result == CompletenessResult.COMPLETE for r in self.completeness_records):
            return CompletenessResult.COMPLETE
        
        return CompletenessResult.INCOMPLETE


# ---------------------------------------------------------------------------
# Experiment: Exact Graph
# ---------------------------------------------------------------------------


def run_exact_graph_experiment() -> dict[str, Any]:
    """Experiment 1: Exact graph with no hidden authorities.
    
    The declared graph perfectly matches the observable mechanisms.
    Expected: COMPLETE
    """
    engine = AuthorityGraphCompletenessEngine()
    
    # Add observable mechanisms (all declared)
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="anchor_001",
        mechanism_type="trust_anchor",
        principal="admin",
        capability="*",
        scope="production",
        source="anchor_001",
        is_declared=True,
    ))
    
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="policy_admin",
        mechanism_type="delegation",
        principal="policy_admin",
        capability="modify_policy",
        scope="production",
        source="anchor_001",
        is_declared=True,
    ))
    
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="execution",
        mechanism_type="delegation",
        principal="execution",
        capability="execute",
        scope="production",
        source="policy_admin",
        is_declared=True,
    ))
    
    records = engine.assess_all_dimensions()
    
    return {
        "experiment": "exact_graph",
        "description": "Exact graph with no hidden authorities",
        "expected": CompletenessResult.COMPLETE,
        "actual": engine.get_overall_completeness(),
        "records": records,
        "hidden_count": len(engine.hidden_authorities),
    }


# ---------------------------------------------------------------------------
# Experiment: Missing Delegation Edge
# ---------------------------------------------------------------------------


def run_missing_edge_experiment() -> dict[str, Any]:
    """Experiment 2: Missing delegation edge.
    
    The actual system has an authority delegation that is not in the
    declared graph.
    Expected: INCOMPLETE (edge coverage)
    """
    engine = AuthorityGraphCompletenessEngine()
    
    # Declared: anchor → policy_admin
    # Actual: anchor → policy_admin → execution (but edge is missing)
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="anchor_001",
        mechanism_type="trust_anchor",
        principal="admin",
        capability="*",
        scope="production",
        source="anchor_001",
        is_declared=True,
    ))
    
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="policy_admin",
        mechanism_type="delegation",
        principal="policy_admin",
        capability="modify_policy",
        scope="production",
        source="anchor_001",
        is_declared=True,
    ))
    
    # This mechanism exists but its edge from policy_admin is not declared
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="execution",
        mechanism_type="delegation",
        principal="execution",
        capability="execute",
        scope="production",
        source="policy_admin",
        is_declared=False,  # Hidden!
    ))
    
    records = engine.assess_all_dimensions()
    
    return {
        "experiment": "missing_edge",
        "description": "Missing delegation edge",
        "expected": CompletenessResult.INCOMPLETE,
        "actual": engine.get_overall_completeness(),
        "records": records,
        "hidden_count": len(engine.hidden_authorities),
    }


# ---------------------------------------------------------------------------
# Experiment: Hidden Authority Node
# ---------------------------------------------------------------------------


def run_hidden_node_experiment() -> dict[str, Any]:
    """Experiment 3: Hidden authority node.
    
    An authority node exists in the system but is not in the declared graph.
    Expected: INCOMPLETE (node coverage)
    """
    engine = AuthorityGraphCompletenessEngine()
    
    # Declared
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="anchor_001",
        mechanism_type="trust_anchor",
        principal="admin",
        capability="*",
        scope="production",
        source="anchor_001",
        is_declared=True,
    ))
    
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="policy_admin",
        mechanism_type="delegation",
        principal="policy_admin",
        capability="modify_policy",
        scope="production",
        source="anchor_001",
        is_declared=True,
    ))
    
    # Hidden node
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="hidden_admin",
        mechanism_type="admin",
        principal="hidden_admin",
        capability="*",
        scope="*",
        source="bootstrap",
        is_declared=False,
        metadata={"out_of_band": True},
    ))
    
    records = engine.assess_all_dimensions()
    
    return {
        "experiment": "hidden_node",
        "description": "Hidden authority node",
        "expected": CompletenessResult.INCOMPLETE,
        "actual": engine.get_overall_completeness(),
        "records": records,
        "hidden_count": len(engine.hidden_authorities),
    }


# ---------------------------------------------------------------------------
# Experiment: Hidden Policy Authority
# ---------------------------------------------------------------------------


def run_hidden_policy_experiment() -> dict[str, Any]:
    """Experiment 4: Hidden policy authority.
    
    A policy authority exists but is not declared in the graph.
    Expected: INCOMPLETE
    """
    engine = AuthorityGraphCompletenessEngine()
    
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="anchor_001",
        mechanism_type="trust_anchor",
        principal="admin",
        capability="*",
        scope="production",
        source="anchor_001",
        is_declared=True,
    ))
    
    # Hidden policy authority
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="hidden_policy",
        mechanism_type="policy",
        principal="policy_engine",
        capability="create_policy",
        scope="production",
        source="bootstrap",
        is_declared=False,
    ))
    
    records = engine.assess_all_dimensions()
    
    return {
        "experiment": "hidden_policy",
        "description": "Hidden policy authority",
        "expected": CompletenessResult.INCOMPLETE,
        "actual": engine.get_overall_completeness(),
        "records": records,
        "hidden_count": len(engine.hidden_authorities),
    }


# ---------------------------------------------------------------------------
# Experiment: Hidden Capability Escalation
# ---------------------------------------------------------------------------


def run_hidden_capability_experiment() -> dict[str, Any]:
    """Experiment 5: Hidden capability escalation.
    
    A capability escalation exists but is not declared.
    Expected: INCOMPLETE
    """
    engine = AuthorityGraphCompletenessEngine()
    
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="anchor_001",
        mechanism_type="trust_anchor",
        principal="admin",
        capability="*",
        scope="production",
        source="anchor_001",
        is_declared=True,
    ))
    
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="service",
        mechanism_type="delegation",
        principal="service",
        capability="read",
        scope="production",
        source="anchor_001",
        is_declared=True,
    ))
    
    # Hidden escalation: service can actually execute
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="service_escalation",
        mechanism_type="capability_escalation",
        principal="service",
        capability="execute",
        scope="production",
        source="service",
        is_declared=False,
    ))
    
    records = engine.assess_all_dimensions()
    
    return {
        "experiment": "hidden_capability",
        "description": "Hidden capability escalation",
        "expected": CompletenessResult.INCOMPLETE,
        "actual": engine.get_overall_completeness(),
        "records": records,
        "hidden_count": len(engine.hidden_authorities),
    }


# ---------------------------------------------------------------------------
# Experiment: Out-of-Band Administrative Authority
# ---------------------------------------------------------------------------


def run_out_of_band_admin_experiment() -> dict[str, Any]:
    """Experiment 6: Out-of-band administrative authority.
    
    An administrative authority exists outside the declared protocol.
    Expected: INCOMPLETE (out-of-band coverage)
    """
    engine = AuthorityGraphCompletenessEngine()
    
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="anchor_001",
        mechanism_type="trust_anchor",
        principal="admin",
        capability="*",
        scope="production",
        source="anchor_001",
        is_declared=True,
    ))
    
    # Out-of-band admin (e.g., root access, SSH key, physical access)
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="root_access",
        mechanism_type="administrative",
        principal="root",
        capability="*",
        scope="*",
        source="physical_access",
        is_declared=False,
        metadata={"out_of_band": True},
    ))
    
    records = engine.assess_all_dimensions()
    
    return {
        "experiment": "out_of_band_admin",
        "description": "Out-of-band administrative authority",
        "expected": CompletenessResult.INCOMPLETE,
        "actual": engine.get_overall_completeness(),
        "records": records,
        "hidden_count": len(engine.hidden_authorities),
    }


# ---------------------------------------------------------------------------
# Experiment: Cross-Domain Hidden Delegation
# ---------------------------------------------------------------------------


def run_cross_domain_hidden_experiment() -> dict[str, Any]:
    """Experiment 7: Cross-domain hidden delegation.
    
    A cross-domain delegation exists but is not declared.
    Expected: INCOMPLETE (cross-domain coverage)
    """
    engine = AuthorityGraphCompletenessEngine()
    
    # Domain A
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="anchor_a",
        mechanism_type="trust_anchor",
        principal="admin_a",
        capability="*",
        scope="domain_a",
        source="anchor_a",
        is_declared=True,
    ))
    
    # Domain B
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="anchor_b",
        mechanism_type="trust_anchor",
        principal="admin_b",
        capability="*",
        scope="domain_b",
        source="anchor_b",
        is_declared=True,
    ))
    
    # Hidden cross-domain delegation
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="cross_domain_grant",
        mechanism_type="cross_domain_delegation",
        principal="admin_a",
        capability="modify_policy",
        scope="domain_b",
        source="anchor_a",
        is_declared=False,
        metadata={"cross_domain": True},
    ))
    
    records = engine.assess_all_dimensions()
    
    return {
        "experiment": "cross_domain_hidden",
        "description": "Cross-domain hidden delegation",
        "expected": CompletenessResult.INCOMPLETE,
        "actual": engine.get_overall_completeness(),
        "records": records,
        "hidden_count": len(engine.hidden_authorities),
    }


# ---------------------------------------------------------------------------
# Experiment: Temporal Authority
# ---------------------------------------------------------------------------


def run_temporal_authority_experiment() -> dict[str, Any]:
    """Experiment 8: Temporal authority that appears only during an interval.
    
    An authority that only exists during a specific time interval.
    Expected: INCOMPLETE (temporal coverage)
    """
    engine = AuthorityGraphCompletenessEngine()
    
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="anchor_001",
        mechanism_type="trust_anchor",
        principal="admin",
        capability="*",
        scope="production",
        source="anchor_001",
        is_declared=True,
    ))
    
    # Temporal authority: only valid during maintenance window
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="maintenance_admin",
        mechanism_type="temporal_delegation",
        principal="maintenance",
        capability="modify_config",
        scope="production",
        source="anchor_001",
        is_declared=False,
        temporal_interval=("2026-01-01T00:00:00", "2026-01-01T04:00:00"),
    ))
    
    records = engine.assess_all_dimensions()
    
    return {
        "experiment": "temporal_authority",
        "description": "Temporal authority during interval",
        "expected": CompletenessResult.INCOMPLETE,
        "actual": engine.get_overall_completeness(),
        "records": records,
        "hidden_count": len(engine.hidden_authorities),
    }


# ---------------------------------------------------------------------------
# Experiment: Failure-Path Authority
# ---------------------------------------------------------------------------


def run_failure_path_experiment() -> dict[str, Any]:
    """Experiment 9: Failure-path authority.
    
    An authority that is activated only on system failure.
    Expected: INCOMPLETE (failure-path coverage)
    """
    engine = AuthorityGraphCompletenessEngine()
    
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="anchor_001",
        mechanism_type="trust_anchor",
        principal="admin",
        capability="*",
        scope="production",
        source="anchor_001",
        is_declared=True,
    ))
    
    # Failure-path authority
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="failover_admin",
        mechanism_type="failure_delegation",
        principal="failover",
        capability="*",
        scope="production",
        source="anchor_001",
        is_declared=False,
        activation_condition="on_failure",
    ))
    
    records = engine.assess_all_dimensions()
    
    return {
        "experiment": "failure_path",
        "description": "Failure-path authority",
        "expected": CompletenessResult.INCOMPLETE,
        "actual": engine.get_overall_completeness(),
        "records": records,
        "hidden_count": len(engine.hidden_authorities),
    }


# ---------------------------------------------------------------------------
# Experiment: Recovery Authority
# ---------------------------------------------------------------------------


def run_recovery_authority_experiment() -> dict[str, Any]:
    """Experiment 10: Recovery authority.
    
    An authority that is activated only during system recovery.
    Expected: INCOMPLETE (recovery coverage)
    """
    engine = AuthorityGraphCompletenessEngine()
    
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="anchor_001",
        mechanism_type="trust_anchor",
        principal="admin",
        capability="*",
        scope="production",
        source="anchor_001",
        is_declared=True,
    ))
    
    # Recovery authority
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="recovery_admin",
        mechanism_type="recovery_delegation",
        principal="recovery",
        capability="*",
        scope="production",
        source="anchor_001",
        is_declared=False,
        activation_condition="on_recovery",
    ))
    
    records = engine.assess_all_dimensions()
    
    return {
        "experiment": "recovery_authority",
        "description": "Recovery authority",
        "expected": CompletenessResult.INCOMPLETE,
        "actual": engine.get_overall_completeness(),
        "records": records,
        "hidden_count": len(engine.hidden_authorities),
    }


# ---------------------------------------------------------------------------
# Experiment: Emergency Override Authority
# ---------------------------------------------------------------------------


def run_emergency_override_experiment() -> dict[str, Any]:
    """Experiment 11: Emergency override authority.
    
    An emergency override authority exists outside the normal graph.
    Expected: INCOMPLETE (emergency coverage)
    """
    engine = AuthorityGraphCompletenessEngine()
    
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="anchor_001",
        mechanism_type="trust_anchor",
        principal="admin",
        capability="*",
        scope="production",
        source="anchor_001",
        is_declared=True,
    ))
    
    # Emergency override
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="emergency_override",
        mechanism_type="emergency_delegation",
        principal="emergency",
        capability="*",
        scope="*",
        source="anchor_001",
        is_declared=False,
        activation_condition="on_emergency",
    ))
    
    records = engine.assess_all_dimensions()
    
    return {
        "experiment": "emergency_override",
        "description": "Emergency override authority",
        "expected": CompletenessResult.INCOMPLETE,
        "actual": engine.get_overall_completeness(),
        "records": records,
        "hidden_count": len(engine.hidden_authorities),
    }


# ---------------------------------------------------------------------------
# Experiment: Authority Mechanism Outside Declared Protocol
# ---------------------------------------------------------------------------


def run_outside_protocol_experiment() -> dict[str, Any]:
    """Experiment 12: Authority mechanism outside declared protocol.
    
    An authority mechanism exists that is entirely outside the declared
    protocol (e.g., a side channel, a backdoor, an undocumented API).
    Expected: INCOMPLETE
    """
    engine = AuthorityGraphCompletenessEngine()
    
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="anchor_001",
        mechanism_type="trust_anchor",
        principal="admin",
        capability="*",
        scope="production",
        source="anchor_001",
        is_declared=True,
    ))
    
    # Outside protocol: undocumented API, side channel, backdoor
    engine.add_observable_mechanism(ObservableAuthorityMechanism(
        mechanism_id="side_channel",
        mechanism_type="side_channel",
        principal="unknown",
        capability="execute",
        scope="production",
        source="undocumented",
        is_declared=False,
        metadata={"out_of_band": True, "protocol": "none"},
    ))
    
    records = engine.assess_all_dimensions()
    
    return {
        "experiment": "outside_protocol",
        "description": "Authority mechanism outside declared protocol",
        "expected": CompletenessResult.INCOMPLETE,
        "actual": engine.get_overall_completeness(),
        "records": records,
        "hidden_count": len(engine.hidden_authorities),
    }


# ---------------------------------------------------------------------------
# Run All Phase 19 Experiments
# ---------------------------------------------------------------------------


def run_all_phase19_experiments() -> dict[str, Any]:
    """Run all Phase 19 experiments."""
    experiments = {
        "exact_graph": run_exact_graph_experiment(),
        "missing_edge": run_missing_edge_experiment(),
        "hidden_node": run_hidden_node_experiment(),
        "hidden_policy": run_hidden_policy_experiment(),
        "hidden_capability": run_hidden_capability_experiment(),
        "out_of_band_admin": run_out_of_band_admin_experiment(),
        "cross_domain_hidden": run_cross_domain_hidden_experiment(),
        "temporal_authority": run_temporal_authority_experiment(),
        "failure_path": run_failure_path_experiment(),
        "recovery_authority": run_recovery_authority_experiment(),
        "emergency_override": run_emergency_override_experiment(),
        "outside_protocol": run_outside_protocol_experiment(),
    }
    
    return {
        "experiments": experiments,
        "total_experiments": len(experiments),
        "complete_count": sum(1 for e in experiments.values() if e["actual"] == CompletenessResult.COMPLETE),
        "incomplete_count": sum(1 for e in experiments.values() if e["actual"] == CompletenessResult.INCOMPLETE),
        "unknown_count": sum(1 for e in experiments.values() if e["actual"] == CompletenessResult.UNKNOWN),
        "total_hidden": sum(e["hidden_count"] for e in experiments.values()),
    }


if __name__ == "__main__":
    results = run_all_phase19_experiments()
    
    print("\n" + "=" * 120)
    print("PHASE 19: AUTHORITY GRAPH COMPLETENESS")
    print("=" * 120)
    
    print(f"\nTotal experiments: {results['total_experiments']}")
    print(f"Complete: {results['complete_count']}")
    print(f"Incomplete: {results['incomplete_count']}")
    print(f"Unknown: {results['unknown_count']}")
    print(f"Total hidden authorities: {results['total_hidden']}")
    
    for name, exp in results["experiments"].items():
        print(f"\n{name}:")
        print(f"  Expected: {exp['expected'].value}")
        print(f"  Actual: {exp['actual'].value}")
        print(f"  Hidden: {exp['hidden_count']}")
        for record in exp.get("records", []):
            print(f"    {record.dimension.value}: {record.result.value}")
