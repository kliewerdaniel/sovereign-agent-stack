"""Phase 20: Authority Under Incomplete Knowledge.

Investigates what authority is permissible when the system cannot establish
that it knows the complete authority graph.

Phase 19 established AUTHORITY_GRAPH_COMPLETENESS_EPISTEMIC: the authority
graph can be incomplete, and completeness is an epistemic property, not
an authority property. The asymmetry: you can prove incompleteness, but
you cannot prove completeness.

Phase 20 asks the harder question:

    WHAT AUTHORITY IS PERMISSIBLE WHEN THE SYSTEM CANNOT ESTABLISH
    THAT IT KNOWS THE COMPLETE AUTHORITY GRAPH?

This is the epistemic authority paradox. The architecture must refuse to
silently promote incomplete authority knowledge into authority, while
still allowing governance to make explicit policy decisions about
uncertainty.

Critical distinctions:
    GRAPH COMPLETENESS ≠ AUTHORITY
    EPISTEMIC STATE ≠ GOVERNANCE DISPOSITION
    GOVERNANCE DISPOSITION ≠ AUTHORITY
    REVALIDATION REQUIREMENT ≠ REVOCATION

Existing infrastructure reused:
- AuthorityGraphCompletenessEngine, CompletenessResult (authority_graph_completeness.py)
- AuthorityGraph, AuthorityGraphNode (authority_genesis.py)
- TrustAnchor, AuthorityDomain (trust_anchor.py)
- AuthoritySurface, AuthorityEnvelope (effect_boundary.py)
- CompletenessScope, CompletenessStatus (dependency_completeness.py)
- PolicyGovernanceEngine, PolicyAuthorityRecord (policy_governance.py)
- GovernancePolicyEngine, Policy, PolicyEvaluationResult (governance_policy.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Completeness State (Four States, Not Three)
# ---------------------------------------------------------------------------


class CompletenessState(str, Enum):
    """Four distinct completeness states.
    
    The fourth state (WAS_COMPLETE_AT_T) is particularly important:
    a historical authorization might have been justified relative to
    the graph observable at T1, while later discovery at T2 reveals
    an authority mechanism that was previously unknown.
    """
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    UNKNOWN = "unknown"
    WAS_COMPLETE_AT_T = "was_complete_at_t"


# ---------------------------------------------------------------------------
# Uncertainty Disposition
# ---------------------------------------------------------------------------


class UncertaintyDisposition(str, Enum):
    """What governance does with uncertainty.
    
    The disposition must come from GOVERNANCE POLICY OVER UNCERTAINTY,
    not from the completeness engine. The completeness engine produces
    epistemic states; governance policy maps them to dispositions.
    """
    HOLD = "hold"
    REVIEW = "review"
    DENY = "deny"
    CONDITIONAL_AUTHORITY = "conditional_authority"
    ESCALATE = "escalate"
    NORMAL = "normal"


# ---------------------------------------------------------------------------
# Authority Under Uncertainty Result
# ---------------------------------------------------------------------------


class AuthorityUnderUncertaintyResult(str, Enum):
    """Result of an authority-under-uncertainty experiment."""
    AUTHORITY_GRANTED = "authority_granted"
    AUTHORITY_CONDITIONAL = "authority_conditional"
    AUTHORITY_DEFERRED = "authority_deferred"
    AUTHORITY_DENIED = "authority_denied"
    REVALIDATION_REQUIRED = "revalidation_required"
    HISTORICAL_PRESERVED = "historical_preserved"
    GOVERNANCE_DISPOSITION_APPLIED = "governance_disposition_applied"
    UNCERTAINTY_NOT_RESOLVED = "uncertainty_not_resolved"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Authority Claim with Provenance and Completeness
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityClaimWithProvenance:
    """An authority claim bundled with its provenance, completeness
    assessment, and temporal validity.
    
    An authority claim is NOT a timeless fact. It is a claim relative
    to a graph snapshot, a completeness assessment, and a temporal
    interval.
    """
    claim_id: str
    principal: str
    capability: str
    scope: str
    authority_id: str
    graph_snapshot_id: str
    completeness_state: CompletenessState
    graph_completeness: float  # 0.0 to 1.0
    temporal_validity: tuple[str, str]
    provenance: tuple[str, ...] = ()
    uncertainty_disposition: UncertaintyDisposition = UncertaintyDisposition.HOLD
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Governance Policy Over Uncertainty
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UncertaintyPolicy:
    """Governance policy that maps completeness states to dispositions.
    
    This is the critical separation: the completeness engine produces
    epistemic states; governance policy maps them to dispositions.
    The disposition is NOT implied by the epistemic state.
    """
    policy_id: str
    name: str
    description: str
    # Mapping from completeness state to disposition
    state_to_disposition: dict[CompletenessState, UncertaintyDisposition] = field(
        default_factory=dict
    )
    # Whether conditional authority is permitted
    conditional_authority_permitted: bool = False
    # Whether revalidation is required on graph drift
    revalidation_on_drift: bool = True
    # Whether historical authorizations are preserved on drift
    preserve_historical_on_drift: bool = True
    
    def get_disposition(
        self, completeness_state: CompletenessState
    ) -> UncertaintyDisposition:
        """Get the governance disposition for a completeness state."""
        return self.state_to_disposition.get(
            completeness_state, UncertaintyDisposition.HOLD
        )


# ---------------------------------------------------------------------------
# Authority Graph Snapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityGraphSnapshot:
    """A snapshot of the authority authority graph at a specific time.
    
    Authority claims are relative to graph snapshots, not to the
    current state of the graph.
    """
    snapshot_id: str
    timestamp: str
    nodes: dict[str, Any] = field(default_factory=dict)
    edges: dict[str, tuple[str, str]] = field(default_factory=dict)
    trust_anchor_ids: set[str] = field(default_factory=set)
    completeness_state: CompletenessState = CompletenessState.UNKNOWN
    completeness_confidence: float = 0.0


# ---------------------------------------------------------------------------
# Authority Under Uncertainty Engine
# ---------------------------------------------------------------------------


@dataclass
class AuthorityUnderUncertaintyEngine:
    """Engine for making authority decisions under incomplete knowledge.
    
    The engine:
    1. Receives an authority claim
    2. Assesses the completeness state of the graph
    3. Applies governance policy over uncertainty
    4. Produces a disposition (NOT authority)
    
    The disposition is then passed to the governance layer for
    authorization.
    """
    
    uncertainty_policy: UncertaintyPolicy = field(default_factory=lambda: UncertaintyPolicy(
        policy_id="default",
        name="Default Uncertainty Policy",
        description="Default policy: HOLD on UNKNOWN, NORMAL on COMPLETE",
        state_to_disposition={
            CompletenessState.COMPLETE: UncertaintyDisposition.NORMAL,
            CompletenessState.INCOMPLETE: UncertaintyDisposition.REVIEW,
            CompletenessState.UNKNOWN: UncertaintyDisposition.HOLD,
            CompletenessState.WAS_COMPLETE_AT_T: UncertaintyDisposition.REVIEW,
        },
    ))
    graph_snapshots: dict[str, AuthorityGraphSnapshot] = field(default_factory=dict)
    authority_claims: list[AuthorityClaimWithProvenance] = field(default_factory=list)
    decisions: list["AuthorityUnderUncertaintyDecision"] = field(default_factory=list)
    
    def create_graph_snapshot(
        self,
        nodes: dict[str, Any],
        edges: dict[str, tuple[str, str]],
        trust_anchor_ids: set[str],
        completeness_state: CompletenessState,
        completeness_confidence: float = 0.0,
    ) -> AuthorityGraphSnapshot:
        """Create a snapshot of the authority graph."""
        snapshot = AuthorityGraphSnapshot(
            snapshot_id=f"snapshot_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(UTC).isoformat(),
            nodes=nodes,
            edges=edges,
            trust_anchor_ids=trust_anchor_ids,
            completeness_state=completeness_state,
            completeness_confidence=completeness_confidence,
        )
        self.graph_snapshots[snapshot.snapshot_id] = snapshot
        return snapshot
    
    def make_authority_decision(
        self,
        principal: str,
        capability: str,
        scope: str,
        authority_id: str,
        graph_snapshot_id: str,
        completeness_state: CompletenessState,
        graph_completeness: float,
        temporal_validity: tuple[str, str] = ("unbounded", "unbounded"),
        provenance: tuple[str, ...] = (),
    ) -> "AuthorityUnderUncertaintyDecision":
        """Make an authority decision under uncertainty.
        
        The decision process:
        1. Create the authority claim with provenance
        2. Apply governance policy over uncertainty
        3. Produce a disposition
        4. Record the decision
        """
        claim = AuthorityClaimWithProvenance(
            claim_id=f"claim_{uuid.uuid4().hex[:12]}",
            principal=principal,
            capability=capability,
            scope=scope,
            authority_id=authority_id,
            graph_snapshot_id=graph_snapshot_id,
            completeness_state=completeness_state,
            graph_completeness=graph_completeness,
            temporal_validity=temporal_validity,
            provenance=provenance,
        )
        self.authority_claims.append(claim)
        
        # Apply governance policy over uncertainty
        disposition = self.uncertainty_policy.get_disposition(completeness_state)
        
        # Determine result based on disposition
        result = self._disposition_to_result(disposition, completeness_state)
        
        decision = AuthorityUnderUncertaintyDecision(
            decision_id=f"decision_{uuid.uuid4().hex[:12]}",
            claim=claim,
            disposition=disposition,
            result=result,
            notes=f"Completeness: {completeness_state.value}, Disposition: {disposition.value}",
        )
        self.decisions.append(decision)
        return decision
    
    def _disposition_to_result(
        self,
        disposition: UncertaintyDisposition,
        completeness_state: CompletenessState,
    ) -> AuthorityUnderUncertaintyResult:
        """Map a disposition to an authority result."""
        if disposition == UncertaintyDisposition.NORMAL:
            return AuthorityUnderUncertaintyResult.AUTHORITY_GRANTED
        elif disposition == UncertaintyDisposition.CONDITIONAL_AUTHORITY:
            return AuthorityUnderUncertaintyResult.AUTHORITY_CONDITIONAL
        elif disposition == UncertaintyDisposition.HOLD:
            return AuthorityUnderUncertaintyResult.AUTHORITY_DEFERRED
        elif disposition == UncertaintyDisposition.DENY:
            return AuthorityUnderUncertaintyResult.AUTHORITY_DENIED
        elif disposition == UncertaintyDisposition.REVIEW:
            return AuthorityUnderUncertaintyResult.REVALIDATION_REQUIRED
        elif disposition == UncertaintyDisposition.ESCALATE:
            return AuthorityUnderUncertaintyResult.UNCERTAINTY_NOT_RESOLVED
        else:
            return AuthorityUnderUncertaintyResult.UNKNOWN
    
    def handle_graph_drift(
        self,
        previous_snapshot_id: str,
        new_completeness_state: CompletenessState,
        new_completeness_confidence: float,
    ) -> "GraphDriftResult":
        """Handle authority graph drift.
        
        When the graph becomes incomplete after prior authorization:
        - Historical decisions are PRESERVED
        - Future authority is RECONSIDERED
        - This is NOT automatic revocation
        """
        previous_snapshot = self.graph_snapshots.get(previous_snapshot_id)
        
        # Find all authority claims based on the previous snapshot
        affected_claims = [
            c for c in self.authority_claims
            if c.graph_snapshot_id == previous_snapshot_id
        ]
        
        # Historical claims are preserved
        historical_preserved = len(affected_claims) > 0
        
        # Revalidation is required for future authority
        revalidation_required = (
            self.uncertainty_policy.revalidation_on_drift
            and new_completeness_state != CompletenessState.COMPLETE
        )
        
        return GraphDriftResult(
            drift_id=f"drift_{uuid.uuid4().hex[:12]}",
            previous_snapshot=previous_snapshot,
            new_completeness_state=new_completeness_state,
            new_completeness_confidence=new_completeness_confidence,
            affected_claims=affected_claims,
            historical_preserved=historical_preserved,
            revalidation_required=revalidation_required,
            automatic_revocation=False,  # NEVER automatic revocation
        )


# ---------------------------------------------------------------------------
# Graph Drift Result
# ---------------------------------------------------------------------------


@dataclass
class GraphDriftResult:
    """Result of authority graph drift."""
    drift_id: str
    previous_snapshot: Optional[AuthorityGraphSnapshot]
    new_completeness_state: CompletenessState
    new_completeness_confidence: float
    affected_claims: list[AuthorityClaimWithProvenance]
    historical_preserved: bool
    revalidation_required: bool
    automatic_revocation: bool  # Always False


# ---------------------------------------------------------------------------
# Authority Under Uncertainty Decision
# ---------------------------------------------------------------------------


@dataclass
class AuthorityUnderUncertaintyDecision:
    """A decision about authority under uncertainty."""
    decision_id: str
    claim: AuthorityClaimWithProvenance
    disposition: UncertaintyDisposition
    result: AuthorityUnderUncertaintyResult
    notes: str = ""


# ---------------------------------------------------------------------------
# Experiment: World A — Known Complete Graph
# ---------------------------------------------------------------------------


def run_world_a_known_complete() -> dict[str, Any]:
    """World A: Known complete authority graph → normal governance."""
    engine = AuthorityUnderUncertaintyEngine()
    
    snapshot = engine.create_graph_snapshot(
        nodes={"anchor": {}, "policy": {}, "execution": {}},
        edges={"e1": ("anchor", "policy"), "e2": ("policy", "execution")},
        trust_anchor_ids={"anchor"},
        completeness_state=CompletenessState.COMPLETE,
        completeness_confidence=1.0,
    )
    
    decision = engine.make_authority_decision(
        principal="execution",
        capability="execute",
        scope="production",
        authority_id="execution",
        graph_snapshot_id=snapshot.snapshot_id,
        completeness_state=CompletenessState.COMPLETE,
        graph_completeness=1.0,
    )
    
    return {
        "world": "A",
        "description": "Known complete graph → normal governance",
        "expected_result": AuthorityUnderUncertaintyResult.AUTHORITY_GRANTED,
        "actual_result": decision.result,
        "disposition": decision.disposition,
    }


# ---------------------------------------------------------------------------
# Experiment: World B — Known Missing Edge
# ---------------------------------------------------------------------------


def run_world_b_missing_edge() -> dict[str, Any]:
    """World B: Known missing authority edge → UNKNOWN epistemic state."""
    engine = AuthorityUnderUncertaintyEngine()
    
    snapshot = engine.create_graph_snapshot(
        nodes={"anchor": {}, "policy": {}},
        edges={"e1": ("anchor", "policy")},
        trust_anchor_ids={"anchor"},
        completeness_state=CompletenessState.INCOMPLETE,
        completeness_confidence=0.7,
    )
    
    decision = engine.make_authority_decision(
        principal="execution",
        capability="execute",
        scope="production",
        authority_id="execution",
        graph_snapshot_id=snapshot.snapshot_id,
        completeness_state=CompletenessState.INCOMPLETE,
        graph_completeness=0.7,
    )
    
    return {
        "world": "B",
        "description": "Known missing edge → UNKNOWN",
        "expected_result": AuthorityUnderUncertaintyResult.REVALIDATION_REQUIRED,
        "actual_result": decision.result,
        "disposition": decision.disposition,
    }


# ---------------------------------------------------------------------------
# Experiment: World C — Unknown Graph Completeness
# ---------------------------------------------------------------------------


def run_world_c_unknown() -> dict[str, Any]:
    """World C: Unknown graph completeness → UNKNOWN."""
    engine = AuthorityUnderUncertaintyEngine()
    
    snapshot = engine.create_graph_snapshot(
        nodes={"anchor": {}},
        edges={},
        trust_anchor_ids={"anchor"},
        completeness_state=CompletenessState.UNKNOWN,
        completeness_confidence=0.0,
    )
    
    decision = engine.make_authority_decision(
        principal="execution",
        capability="execute",
        scope="production",
        authority_id="execution",
        graph_snapshot_id=snapshot.snapshot_id,
        completeness_state=CompletenessState.UNKNOWN,
        graph_completeness=0.0,
    )
    
    return {
        "world": "C",
        "description": "Unknown completeness → UNKNOWN",
        "expected_result": AuthorityUnderUncertaintyResult.AUTHORITY_DEFERRED,
        "actual_result": decision.result,
        "disposition": decision.disposition,
    }


# ---------------------------------------------------------------------------
# Experiment: World D — Hidden Authority Outside Observation
# ---------------------------------------------------------------------------


def run_world_d_hidden_authority() -> dict[str, Any]:
    """World D: Hidden authority exists but is outside observation → UNKNOWN."""
    engine = AuthorityUnderUncertaintyEngine()
    
    # Declared graph is complete
    snapshot = engine.create_graph_snapshot(
        nodes={"anchor": {}, "policy": {}},
        edges={"e1": ("anchor", "policy")},
        trust_anchor_ids={"anchor"},
        completeness_state=CompletenessState.COMPLETE,
        completeness_confidence=0.9,  # Not 1.0 because hidden authority may exist
    )
    
    # But there's a hidden authority outside observation
    decision = engine.make_authority_decision(
        principal="execution",
        capability="execute",
        scope="production",
        authority_id="execution",
        graph_snapshot_id=snapshot.snapshot_id,
        completeness_state=CompletenessState.INCOMPLETE,
        graph_completeness=0.9,
        provenance=("hidden_authority_outside_observation",),
    )
    
    return {
        "world": "D",
        "description": "Hidden authority outside observation → UNKNOWN",
        "expected_result": AuthorityUnderUncertaintyResult.REVALIDATION_REQUIRED,
        "actual_result": decision.result,
        "disposition": decision.disposition,
    }


# ---------------------------------------------------------------------------
# Experiment: World E — Hidden Authority Discovered After Authorization
# ---------------------------------------------------------------------------


def run_world_e_discovered_after() -> dict[str, Any]:
    """World E: Hidden authority discovered after authorization.
    
    Historical decision is PRESERVED.
    Future authority is RECONSIDERED.
    """
    engine = AuthorityUnderUncertaintyEngine()
    
    # T1: Graph appears complete
    snapshot_t1 = engine.create_graph_snapshot(
        nodes={"anchor": {}, "policy": {}, "execution": {}},
        edges={"e1": ("anchor", "policy"), "e2": ("policy", "execution")},
        trust_anchor_ids={"anchor"},
        completeness_state=CompletenessState.COMPLETE,
        completeness_confidence=1.0,
    )
    
    # Authorization at T1
    decision_t1 = engine.make_authority_decision(
        principal="execution",
        capability="execute",
        scope="production",
        authority_id="execution",
        graph_snapshot_id=snapshot_t1.snapshot_id,
        completeness_state=CompletenessState.COMPLETE,
        graph_completeness=1.0,
    )
    
    # T2: Hidden authority discovered
    drift_result = engine.handle_graph_drift(
        previous_snapshot_id=snapshot_t1.snapshot_id,
        new_completeness_state=CompletenessState.INCOMPLETE,
        new_completeness_confidence=0.8,
    )
    
    return {
        "world": "E",
        "description": "Hidden authority discovered after authorization",
        "expected_result": AuthorityUnderUncertaintyResult.HISTORICAL_PRESERVED,
        "t1_result": decision_t1.result,
        "drift_result": drift_result,
        "historical_preserved": drift_result.historical_preserved,
        "revalidation_required": drift_result.revalidation_required,
        "automatic_revocation": drift_result.automatic_revocation,
    }


# ---------------------------------------------------------------------------
# Experiment: World F — Hidden Authority in Emergency Path
# ---------------------------------------------------------------------------


def run_world_f_emergency_path() -> dict[str, Any]:
    """World F: Hidden authority appears only during emergency path."""
    engine = AuthorityUnderUncertaintyEngine()
    
    # Normal graph is complete
    snapshot = engine.create_graph_snapshot(
        nodes={"anchor": {}, "policy": {}, "execution": {}},
        edges={"e1": ("anchor", "policy"), "e2": ("policy", "execution")},
        trust_anchor_ids={"anchor"},
        completeness_state=CompletenessState.COMPLETE,
        completeness_confidence=1.0,
    )
    
    # But emergency path has hidden authority
    decision = engine.make_authority_decision(
        principal="emergency_executor",
        capability="execute",
        scope="production",
        authority_id="emergency_execution",
        graph_snapshot_id=snapshot.snapshot_id,
        completeness_state=CompletenessState.UNKNOWN,
        graph_completeness=0.5,
        provenance=("emergency_path_hidden_authority",),
    )
    
    return {
        "world": "F",
        "description": "Hidden authority in emergency path",
        "expected_result": AuthorityUnderUncertaintyResult.AUTHORITY_DEFERRED,
        "actual_result": decision.result,
        "disposition": decision.disposition,
    }


# ---------------------------------------------------------------------------
# Experiment: World G — Hidden Cross-Domain Delegation
# ---------------------------------------------------------------------------


def run_world_g_cross_domain() -> dict[str, Any]:
    """World G: Hidden cross-domain delegation → domain sovereignty uncertainty."""
    engine = AuthorityUnderUncertaintyEngine()
    
    # Domain A graph is complete
    snapshot = engine.create_graph_snapshot(
        nodes={"anchor_a": {}, "policy_a": {}},
        edges={"e1": ("anchor_a", "policy_a")},
        trust_anchor_ids={"anchor_a"},
        completeness_state=CompletenessState.COMPLETE,
        completeness_confidence=1.0,
    )
    
    # But cross-domain delegation to Domain B is hidden
    decision = engine.make_authority_decision(
        principal="policy_a",
        capability="modify_policy",
        scope="domain_b",  # Cross-domain!
        authority_id="cross_domain_modification",
        graph_snapshot_id=snapshot.snapshot_id,
        completeness_state=CompletenessState.INCOMPLETE,
        graph_completeness=0.6,
        provenance=("hidden_cross_domain_delegation",),
    )
    
    return {
        "world": "G",
        "description": "Hidden cross-domain delegation",
        "expected_result": AuthorityUnderUncertaintyResult.REVALIDATION_REQUIRED,
        "actual_result": decision.result,
        "disposition": decision.disposition,
    }


# ---------------------------------------------------------------------------
# Experiment: World H — Graph Becomes Incomplete After Prior Authorization
# ---------------------------------------------------------------------------


def run_world_h_becomes_incomplete() -> dict[str, Any]:
    """World H: Graph becomes incomplete after prior authorization.
    
    Revalidation is required.
    Automatic revocation does NOT happen.
    """
    engine = AuthorityUnderUncertaintyEngine()
    
    # T1: Graph is complete
    snapshot_t1 = engine.create_graph_snapshot(
        nodes={"anchor": {}, "policy": {}, "execution": {}},
        edges={"e1": ("anchor", "policy"), "e2": ("policy", "execution")},
        trust_anchor_ids={"anchor"},
        completeness_state=CompletenessState.COMPLETE,
        completeness_confidence=1.0,
    )
    
    # Authorization at T1
    decision_t1 = engine.make_authority_decision(
        principal="execution",
        capability="execute",
        scope="production",
        authority_id="execution",
        graph_snapshot_id=snapshot_t1.snapshot_id,
        completeness_state=CompletenessState.COMPLETE,
        graph_completeness=1.0,
    )
    
    # T2: Graph becomes incomplete (new hidden authority discovered)
    drift_result = engine.handle_graph_drift(
        previous_snapshot_id=snapshot_t1.snapshot_id,
        new_completeness_state=CompletenessState.INCOMPLETE,
        new_completeness_confidence=0.7,
    )
    
    return {
        "world": "H",
        "description": "Graph becomes incomplete after authorization",
        "t1_result": decision_t1.result,
        "drift_result": drift_result,
        "revalidation_required": drift_result.revalidation_required,
        "automatic_revocation": drift_result.automatic_revocation,
        "historical_preserved": drift_result.historical_preserved,
    }


# ---------------------------------------------------------------------------
# Experiment: Adversarial — Observation Gap Attack
# ---------------------------------------------------------------------------


def run_adversarial_observation_gap() -> dict[str, Any]:
    """Adversarial: Attacker causes observation gap to hide second authority.
    
    Legitimate authority graph + incomplete observation → incorrectly
    bounded knowledge of authority.
    
    This is a different failure mode from Phase 14:
    - Phase 14: Legitimate authority → policy transformation → excessive effect
    - Phase 20: Legitimate graph → incomplete observation → incorrect bounds
    """
    engine = AuthorityUnderUncertaintyEngine()
    
    # Legitimate graph
    snapshot = engine.create_graph_snapshot(
        nodes={"anchor": {}, "policy": {}, "execution": {}},
        edges={"e1": ("anchor", "policy"), "e2": ("policy", "execution")},
        trust_anchor_ids={"anchor"},
        completeness_state=CompletenessState.COMPLETE,
        completeness_confidence=0.95,  # Not 1.0 because observation may be gamed
    )
    
    # Attacker's hidden authority is outside the observation boundary
    decision = engine.make_authority_decision(
        principal="attacker",
        capability="execute",
        scope="production",
        authority_id="hidden_execution",
        graph_snapshot_id=snapshot.snapshot_id,
        completeness_state=CompletenessState.INCOMPLETE,
        graph_completeness=0.95,
        provenance=("observation_gap_attack",),
    )
    
    return {
        "world": "ADVERSARIAL",
        "description": "Observation gap attack",
        "expected_result": AuthorityUnderUncertaintyResult.REVALIDATION_REQUIRED,
        "actual_result": decision.result,
        "disposition": decision.disposition,
    }


# ---------------------------------------------------------------------------
# Experiment: WAS_COMPLETE_AT_T
# ---------------------------------------------------------------------------


def run_was_complete_at_t() -> dict[str, Any]:
    """Test the WAS_COMPLETE_AT_T state.
    
    A historical authorization was justified relative to the graph
    observable at T1, while later discovery at T2 reveals an authority
    mechanism that was previously unknown.
    """
    engine = AuthorityUnderUncertaintyEngine()
    
    # T1: Graph was complete
    snapshot_t1 = engine.create_graph_snapshot(
        nodes={"anchor": {}, "policy": {}, "execution": {}},
        edges={"e1": ("anchor", "policy"), "e2": ("policy", "execution")},
        trust_anchor_ids={"anchor"},
        completeness_state=CompletenessState.WAS_COMPLETE_AT_T,
        completeness_confidence=1.0,
    )
    
    # Historical authorization at T1
    decision_t1 = engine.make_authority_decision(
        principal="execution",
        capability="execute",
        scope="production",
        authority_id="execution",
        graph_snapshot_id=snapshot_t1.snapshot_id,
        completeness_state=CompletenessState.WAS_COMPLETE_AT_T,
        graph_completeness=1.0,
        temporal_validity=("2026-01-01T00:00:00", "2026-01-01T01:00:00"),
    )
    
    return {
        "world": "WAS_COMPLETE_AT_T",
        "description": "Graph was complete at T1, now uncertain",
        "expected_result": AuthorityUnderUncertaintyResult.REVALIDATION_REQUIRED,
        "actual_result": decision_t1.result,
        "disposition": decision_t1.disposition,
    }


# ---------------------------------------------------------------------------
# Run All Phase 20 Experiments
# ---------------------------------------------------------------------------


def run_all_phase20_experiments() -> dict[str, Any]:
    """Run all Phase 20 experiments."""
    experiments = {
        "world_a": run_world_a_known_complete(),
        "world_b": run_world_b_missing_edge(),
        "world_c": run_world_c_unknown(),
        "world_d": run_world_d_hidden_authority(),
        "world_e": run_world_e_discovered_after(),
        "world_f": run_world_f_emergency_path(),
        "world_g": run_world_g_cross_domain(),
        "world_h": run_world_h_becomes_incomplete(),
        "adversarial": run_adversarial_observation_gap(),
        "was_complete_at_t": run_was_complete_at_t(),
    }
    
    return {
        "experiments": experiments,
        "total_experiments": len(experiments),
        "authority_granted_count": sum(
            1 for e in experiments.values()
            if e.get("actual_result") == AuthorityUnderUncertaintyResult.AUTHORITY_GRANTED
        ),
        "authority_deferred_count": sum(
            1 for e in experiments.values()
            if e.get("actual_result") == AuthorityUnderUncertaintyResult.AUTHORITY_DEFERRED
        ),
        "revalidation_required_count": sum(
            1 for e in experiments.values()
            if e.get("actual_result") == AuthorityUnderUncertaintyResult.REVALIDATION_REQUIRED
            or e.get("revalidation_required")
        ),
        "historical_preserved_count": sum(
            1 for e in experiments.values()
            if e.get("historical_preserved")
        ),
        "automatic_revocation_count": sum(
            1 for e in experiments.values()
            if e.get("automatic_revocation")
        ),
    }


if __name__ == "__main__":
    results = run_all_phase20_experiments()
    
    print("\n" + "=" * 120)
    print("PHASE 20: AUTHORITY UNDER INCOMPLETE KNOWLEDGE")
    print("=" * 120)
    
    print(f"\nTotal experiments: {results['total_experiments']}")
    print(f"Authority granted: {results['authority_granted_count']}")
    print(f"Authority deferred: {results['authority_deferred_count']}")
    print(f"Revalidation required: {results['revalidation_required_count']}")
    print(f"Historical preserved: {results['historical_preserved_count']}")
    print(f"Automatic revocation: {results['automatic_revocation_count']}")
    
    for name, exp in results["experiments"].items():
        print(f"\n{name}:")
        print(f"  Description: {exp['description']}")
        if "actual_result" in exp:
            print(f"  Result: {exp['actual_result'].value}")
        if "disposition" in exp:
            print(f"  Disposition: {exp['disposition'].value}")
        if "historical_preserved" in exp:
            print(f"  Historical preserved: {exp['historical_preserved']}")
        if "revalidation_required" in exp:
            print(f"  Revalidation required: {exp['revalidation_required']}")
        if "automatic_revocation" in exp:
            print(f"  Automatic revocation: {exp['automatic_revocation']}")
