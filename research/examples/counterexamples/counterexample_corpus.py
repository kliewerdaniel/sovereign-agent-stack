"""Counterexample Corpus for Sovereign Agent Stack.

A counterexample is an architectural discovery: a case where the system
behaved in a way that reveals an implicit semantic boundary.

Counterexamples are first-class research artifacts.
They persist even after the code is changed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class CounterexampleType(str, Enum):
    """Types of counterexamples."""
    PROTOCOL_BUG = "protocol_bug"
    MISSING_SEMANTICS = "missing_semantics"
    OVERLY_CONSERVATIVE_POLICY = "overly_conservative_policy"
    VALID_REJECTION = "valid_rejection"
    AMBIGUOUS_SEMANTICS = "ambiguous_semantics"
    EPISTEMIC_ERROR = "epistemic_error"
    AUTHORITY_ERROR = "authority_error"
    COMPOSITION_ERROR = "composition_error"
    TEMPORAL_ERROR = "temporal_error"
    PROVENANCE_ERROR = "provenance_error"
    GOVERNANCE_CONFLICT = "governance_conflict"
    EXPECTED_BEHAVIOR = "expected_behavior"
    UNRESOLVED = "unresolved"


class ResolutionStatus(str, Enum):
    """Resolution status of a counterexample."""
    UNRESOLVED = "unresolved"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"
    NOT_A_BUG = "not_a_bug"


@dataclass(frozen=True)
class Counterexample:
    """A counterexample: an architectural discovery."""
    counterexample_id: str
    timestamp: str
    counterexample_type: CounterexampleType
    title: str
    description: str
    original_assumption: str
    world_state: dict[str, Any]
    agent_state: dict[str, Any]
    proposal: dict[str, Any]
    authority_state: dict[str, Any]
    observed_failure: str
    expected_behavior: str
    actual_behavior: str
    classification: str
    provenance: list[str]
    reproduction_procedure: list[str]
    resolution_status: ResolutionStatus = ResolutionStatus.UNRESOLVED
    resolution_notes: str = ""
    resolution_timestamp: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "counterexample_id": self.counterexample_id,
            "timestamp": self.timestamp,
            "counterexample_type": self.counterexample_type.value,
            "title": self.title,
            "description": self.description,
            "original_assumption": self.original_assumption,
            "world_state": self.world_state,
            "agent_state": self.agent_state,
            "proposal": self.proposal,
            "authority_state": self.authority_state,
            "observed_failure": self.observed_failure,
            "expected_behavior": self.expected_behavior,
            "actual_behavior": self.actual_behavior,
            "classification": self.classification,
            "provenance": self.provenance,
            "reproduction_procedure": self.reproduction_procedure,
            "resolution_status": self.resolution_status.value,
            "resolution_notes": self.resolution_notes,
            "resolution_timestamp": self.resolution_timestamp,
        }


@dataclass
class CounterexampleCorpus:
    """A collection of counterexamples."""
    counterexamples: list[Counterexample] = field(default_factory=list)

    def add(self, counterexample: Counterexample) -> None:
        """Add a counterexample to the corpus."""
        self.counterexamples.append(counterexample)

    def get_by_type(self, ce_type: CounterexampleType) -> list[Counterexample]:
        """Get counterexamples by type."""
        return [ce for ce in self.counterexamples if ce.counterexample_type == ce_type]

    def get_by_status(self, status: ResolutionStatus) -> list[Counterexample]:
        """Get counterexamples by resolution status."""
        return [ce for ce in self.counterexamples if ce.resolution_status == status]

    def get_unresolved(self) -> list[Counterexample]:
        """Get unresolved counterexamples."""
        return self.get_by_status(ResolutionStatus.UNRESOLVED)

    def get_resolved(self) -> list[Counterexample]:
        """Get resolved counterexamples."""
        return self.get_by_status(ResolutionStatus.RESOLVED)

    def count_by_type(self) -> dict[str, int]:
        """Count counterexamples by type."""
        counts: dict[str, int] = {}
        for ce in self.counterexamples:
            t = ce.counterexample_type.value
            counts[t] = counts.get(t, 0) + 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_count": len(self.counterexamples),
            "unresolved_count": len(self.get_unresolved()),
            "resolved_count": len(self.get_resolved()),
            "type_counts": self.count_by_type(),
            "counterexamples": [ce.to_dict() for ce in self.counterexamples],
        }


def build_initial_counterexamples() -> CounterexampleCorpus:
    """Build the initial counterexample corpus with discovered counterexamples."""
    corpus = CounterexampleCorpus()

    # COUNTEREXAMPLE-001
    corpus.add(Counterexample(
        counterexample_id="COUNTEREXAMPLE-001",
        timestamp=datetime.utcnow().isoformat(),
        counterexample_type=CounterexampleType.UNRESOLVED,
        title="Evidence arrives after authorization",
        description=(
            "New evidence arrives after authorization has been materialized. "
            "The protocol currently classifies this as INCONCLUSIVE. "
            "The question is whether the authorization should be suspended "
            "pending evaluation of the new evidence against the authorization's "
            "epistemic dependency set."
        ),
        original_assumption="Authorization remains valid once materialized regardless of new evidence.",
        world_state={
            "time": "T7",
            "authorization_time": "T4",
            "evidence_discovery_time": "T5",
            "execution_request_time": "T7",
        },
        agent_state={
            "current_proposition": "P",
            "confidence": 0.8,
            "evidence_at_authorization": ["E1", "E2"],
            "new_evidence": ["E3"],
        },
        proposal={
            "action": "process_payment",
            "resource": "provider_a",
            "authorization_ref": "auth_001",
        },
        authority_state={
            "authorization": "auth_001",
            "status": "valid",
            "epistemic_dependency_set": ["E1", "E2", "P"],
        },
        observed_failure="New evidence E3 is not evaluated against authorization's epistemic dependencies.",
        expected_behavior="Authorization should be suspended pending evaluation of E3 against epistemic dependency set.",
        actual_behavior="Authorization remains valid; new evidence is ignored.",
        classification="MISSING_SEMANTICS",
        provenance=["multi_agent_trial", "authority_races"],
        reproduction_procedure=[
            "1. Agent proposes action with evidence E1, E2",
            "2. Governance approves authorization based on E1, E2",
            "3. New evidence E3 arrives contradicting P",
            "4. Agent requests execution",
            "5. Observe whether authorization is re-evaluated",
        ],
    ))

    # COUNTEREXAMPLE-002
    corpus.add(Counterexample(
        counterexample_id="COUNTEREXAMPLE-002",
        timestamp=datetime.utcnow().isoformat(),
        counterexample_type=CounterexampleType.OVERLY_CONSERVATIVE_POLICY,
        title="Individually valid sequential proposals conflict",
        description=(
            "Two individually valid proposals (backup_database, replace_provider) "
            "are rejected by the composition engine because they target the same resource. "
            "However, the second action depends on the first: backup must complete before "
            "replace. This is a dependency chain, not a conflict."
        ),
        original_assumption="Multiple proposals targeting the same resource are always conflicting.",
        world_state={
            "resource": "payment_database",
            "current_state": "active",
            "backup_status": "not_started",
        },
        agent_state={
            "proposals": ["backup_database", "replace_provider"],
            "individual_validity": True,
        },
        proposal={
            "sequence": ["backup_database", "replace_provider", "verify_provider"],
        },
        authority_state={
            "backup_authorization": "valid",
            "replace_authorization": "valid",
        },
        observed_failure="Sequential dependency chain is rejected as resource conflict.",
        expected_behavior="Proposals should be recognized as sequential dependency, not conflict.",
        actual_behavior="Composition engine rejects all same-resource proposals as conflicting.",
        classification="MISSING_SEMANTICS",
        provenance=["multi_agent_trial", "agent_composition"],
        reproduction_procedure=[
            "1. Create proposal A: backup_database",
            "2. Create proposal B: replace_provider",
            "3. Set B's prerequisite = A's postcondition",
            "4. Build intent graph",
            "5. Observe whether graph detects sequential dependency vs conflict",
        ],
    ))

    # COUNTEREXAMPLE-003
    corpus.add(Counterexample(
        counterexample_id="COUNTEREXAMPLE-003",
        timestamp=datetime.utcnow().isoformat(),
        counterexample_type=CounterexampleType.COMPOSITION_ERROR,
        title="Two independently valid agents propose incompatible remediations",
        description=(
            "Researcher proposes replacing provider A with provider B. "
            "Operator proposes disabling provider A. "
            "Both proposals are individually valid but mutually exclusive. "
            "The protocol correctly identifies the conflict but lacks semantics "
            "for resolution beyond rejection."
        ),
        original_assumption="Individually valid proposals should be composable.",
        world_state={
            "provider_a": "active",
            "provider_b": "standby",
        },
        agent_state={
            "researcher_proposal": "replace A with B",
            "operator_proposal": "disable A",
        },
        proposal={
            "type": "remediation",
            "targets": ["provider_a"],
        },
        authority_state={
            "researcher_authorization": "valid",
            "operator_authorization": "valid",
        },
        observed_failure="Valid but incompatible proposals cannot be composed.",
        expected_behavior="Protocol should detect incompatibility and represent it explicitly.",
        actual_behavior="Both proposals are rejected when composed.",
        classification="EXPECTED_BEHAVIOR",
        provenance=["multi_agent_trial"],
        reproduction_procedure=[
            "1. Researcher proposes replace(A, B)",
            "2. Operator proposes disable(A)",
            "3. Both have valid authorization",
            "4. Attempt to compose",
            "5. Observe conflict detection",
        ],
    ))

    # COUNTEREXAMPLE-004
    corpus.add(Counterexample(
        counterexample_id="COUNTEREXAMPLE-004",
        timestamp=datetime.utcnow().isoformat(),
        counterexample_type=CounterexampleType.TEMPORAL_ERROR,
        title="Prerequisite action changes assumptions of dependent action",
        description=(
            "Action A (backup_database) completes successfully. "
            "Action B (replace_provider) was authorized based on assumptions "
            "that held before A executed. A's execution changed the world state "
            "in a way that invalidates B's assumptions."
        ),
        original_assumption="Authorization of a plan is valid if all components are individually valid at plan creation time.",
        world_state={
            "pre_A": {"database": "active", "provider": "A"},
            "post_A": {"database": "backed_up", "provider": "A"},
            "pre_B": {"database": "backed_up", "provider": "A"},
        },
        agent_state={
            "plan": ["backup_database", "replace_provider"],
            "assumptions": ["database_is_active"],
        },
        proposal={
            "B": "replace_provider",
            "B_assumptions": ["database_is_active"],
        },
        authority_state={
            "B_authorization": "valid",
            "B_authorized_at": "before_A",
        },
        observed_failure="B's assumptions are stale after A executes but B's authorization is unchanged.",
        expected_behavior="Dependent action's assumptions should be revalidated after prerequisite execution.",
        actual_behavior="Authorization remains valid even though assumptions changed.",
        classification="MISSING_SEMANTICS",
        provenance=["multi_agent_trial", "authority_races"],
        reproduction_procedure=[
            "1. Create plan A -> B",
            "2. Authorize A and B independently",
            "3. Execute A",
            "4. Verify B's assumptions still hold",
            "5. Observe whether stale assumptions invalidate B",
        ],
    ))

    # COUNTEREXAMPLE-005
    corpus.add(Counterexample(
        counterexample_id="COUNTEREXAMPLE-005",
        timestamp=datetime.utcnow().isoformat(),
        counterexample_type=CounterexampleType.TEMPORAL_ERROR,
        title="Authorization valid when created but world changes before execution",
        description=(
            "Authorization is materialized at T1. "
            "World state changes at T2. "
            "Execution requested at T3. "
            "The authorization was valid at T1 but the world no longer supports it."
        ),
        original_assumption="Authorization validity is independent of world state changes.",
        world_state={
            "T1": {"provider": "A", "policy": "allow"},
            "T2": {"provider": "B", "policy": "prohibit"},
            "T3": {"provider": "B", "policy": "prohibit"},
        },
        agent_state={
            "authorization": "auth_001",
            "authorized_at": "T1",
        },
        proposal={
            "action": "process_payment",
            "resource": "provider_a",
            "authorization_ref": "auth_001",
        },
        authority_state={
            "auth_001": "valid",
            "resource_at_authorization": "provider_a",
            "resource_at_execution": "provider_b",
        },
        observed_failure="Authorization does not track resource state changes.",
        expected_behavior="Authorization should be revalidated against current world state at execution.",
        actual_behavior="Authorization remains valid; execution proceeds against wrong resource.",
        classification="MISSING_SEMANTICS",
        provenance=["authority_races", "toctou"],
        reproduction_procedure=[
            "1. Create authorization for resource A",
            "2. World changes: resource A -> B",
            "3. Request execution",
            "4. Observe whether authorization is checked against current state",
        ],
    ))

    # COUNTEREXAMPLE-006
    corpus.add(Counterexample(
        counterexample_id="COUNTEREXAMPLE-006",
        timestamp=datetime.utcnow().isoformat(),
        counterexample_type=CounterexampleType.EPISTEMIC_ERROR,
        title="Capability remains syntactically valid while its epistemic basis changes",
        description=(
            "A capability is issued based on evidence E1, E2 supporting proposition P. "
            "New evidence E3 arrives that refutes P. "
            "The capability remains syntactically valid (properly signed, within temporal bounds) "
            "but its epistemic foundation has been undermined."
        ),
        original_assumption="Syntactic validity of capability implies operational validity.",
        world_state={
            "evidence": ["E1", "E2"],
            "proposition_P": "supported",
        },
        agent_state={
            "capability": "cap_001",
            "capability_status": "valid",
            "epistemic_basis": ["E1", "E2", "P"],
        },
        proposal={
            "action": "process_payment",
            "capability_ref": "cap_001",
        },
        authority_state={
            "cap_001": {
                "status": "valid",
                "epistemic_dependencies": ["E1", "E2", "P"],
            },
        },
        observed_failure="Capability validity is not tied to epistemic basis.",
        expected_behavior="Capability should be suspended when epistemic basis changes.",
        actual_behavior="Capability remains valid regardless of epistemic changes.",
        classification="MISSING_SEMANTICS",
        provenance=["multi_agent_trial", "authority_races"],
        reproduction_procedure=[
            "1. Issue capability based on E1, E2, P",
            "2. New evidence E3 refutes P",
            "3. Attempt to use capability",
            "4. Observe whether epistemic basis is re-evaluated",
        ],
    ))

    # COUNTEREXAMPLE-007
    corpus.add(Counterexample(
        counterexample_id="COUNTEREXAMPLE-007",
        timestamp=datetime.utcnow().isoformat(),
        counterexample_type=CounterexampleType.AMBIGUOUS_SEMANTICS,
        title="Two agents have valid but incompatible epistemic states",
        description=(
            "Researcher concludes provider B is active based on runtime traces. "
            "Auditor concludes provider B is configured but not active based on configuration. "
            "Both conclusions are valid given their evidence but incompatible. "
            "The protocol has no semantics for resolving epistemic conflicts "
            "without resorting to confidence, recency, or role."
        ),
        original_assumption="Agents operating on the same world will have consistent epistemic states.",
        world_state={
            "provider_b": {
                "configured": True,
                "runtime_active": True,
            },
        },
        agent_state={
            "researcher": {
                "evidence": ["runtime_traces"],
                "conclusion": "active",
            },
            "auditor": {
                "evidence": ["configuration"],
                "conclusion": "configured_not_active",
            },
        },
        proposal={
            "type": "epistemic_conflict",
        },
        authority_state={
            "researcher_authorization": "valid",
            "auditor_authorization": "valid",
        },
        observed_failure="Protocol cannot resolve epistemic conflicts without violating invariants.",
        expected_behavior="Protocol should represent the conflict explicitly and defer to governance.",
        actual_behavior="Both epistemic states are preserved; no resolution mechanism exists.",
        classification="EXPECTED_BEHAVIOR",
        provenance=["multi_agent_trial", "agent_disagreement"],
        reproduction_procedure=[
            "1. Researcher observes runtime traces",
            "2. Auditor observes configuration",
            "3. Both derive valid but incompatible conclusions",
            "4. Attempt to resolve through protocol",
            "5. Observe whether resolution violates invariants",
        ],
    ))

    # COUNTEREXAMPLE-008
    corpus.add(Counterexample(
        counterexample_id="COUNTEREXAMPLE-008",
        timestamp=datetime.utcnow().isoformat(),
        counterexample_type=CounterexampleType.AUTHORITY_ERROR,
        title="Remediation invalidates another agent's planned execution",
        description=(
            "Operator plans to execute action X at T3. "
            "Researcher executes remediation Y at T2. "
            "Y changes the world state such that X's authorization is no longer valid. "
            "X's authorization was valid when planned but is now stale."
        ),
        original_assumption="Authorizations are independent of other agents' actions.",
        world_state={
            "T1": {"provider": "A", "feature_flag": "enabled"},
            "T2": {"provider": "B", "feature_flag": "disabled"},
            "T3": {"provider": "B", "feature_flag": "disabled"},
        },
        agent_state={
            "operator": {
                "planned_action": "X",
                "authorization": "auth_X",
            },
            "researcher": {
                "executed_action": "Y",
            },
        },
        proposal={
            "X": "process_payment",
            "Y": "replace_provider",
        },
        authority_state={
            "auth_X": {
                "status": "valid",
                "resource": "provider_a",
                "current_resource": "provider_b",
            },
        },
        observed_failure="Agent Y's remediation invalidates Agent X's authorization.",
        expected_behavior="Cross-agent authorization invalidation should be detected.",
        actual_behavior="Agent X's authorization remains valid despite world change.",
        classification="MISSING_SEMANTICS",
        provenance=["multi_agent_trial"],
        reproduction_procedure=[
            "1. Operator obtains authorization for X",
            "2. Researcher executes Y which changes the world",
            "3. Operator attempts X",
            "4. Observe whether cross-agent invalidation is detected",
        ],
    ))

    # COUNTEREXAMPLE-009
    corpus.add(Counterexample(
        counterexample_id="COUNTEREXAMPLE-009",
        timestamp=datetime.utcnow().isoformat(),
        counterexample_type=CounterexampleType.AMBIGUOUS_SEMANTICS,
        title="New observation relevant to one authorization but irrelevant to another",
        description=(
            "Authorization A depends on proposition P1. "
            "Authorization B depends on proposition P2. "
            "New evidence refutes P1 but not P2. "
            "The protocol must determine whether A and B are both invalidated, "
            "or only A."
        ),
        original_assumption="All new evidence is equally relevant to all authorizations.",
        world_state={
            "P1": "refuted",
            "P2": "supported",
        },
        agent_state={
            "authorization_A": {
                "dependencies": ["P1"],
            },
            "authorization_B": {
                "dependencies": ["P2"],
            },
        },
        proposal={
            "new_evidence": "E_new",
        },
        authority_state={
            "A": "should_be_invalidated",
            "B": "should_remain_valid",
        },
        observed_failure="Protocol does not track per-authorization epistemic dependencies.",
        expected_behavior="Only A should be invalidated; B should remain valid.",
        actual_behavior="Both authorizations are evaluated uniformly.",
        classification="MISSING_SEMANTICS",
        provenance=["multi_agent_trial"],
        reproduction_procedure=[
            "1. Create authorization A dependent on P1",
            "2. Create authorization B dependent on P2",
            "3. New evidence refutes P1",
            "4. Observe whether A and B are differentially invalidated",
        ],
    ))

    # COUNTEREXAMPLE-010
    corpus.add(Counterexample(
        counterexample_id="COUNTEREXAMPLE-010",
        timestamp=datetime.utcnow().isoformat(),
        counterexample_type=CounterexampleType.MISSING_SEMANTICS,
        title="Valid execution plan contains cross-domain operation",
        description=(
            "A plan includes an operation that crosses from the payment domain "
            "to the identity domain. Both domains have valid authorizations, "
            "but the cross-domain operation requires explicit bridging authority "
            "that does not exist."
        ),
        original_assumption="Valid authorizations in each domain imply valid cross-domain operations.",
        world_state={
            "payment_domain": {"authorization": "valid"},
            "identity_domain": {"authorization": "valid"},
        },
        agent_state={
            "plan": ["process_payment", "modify_identity"],
            "domain_authorizations": ["payment_auth", "identity_auth"],
        },
        proposal={
            "type": "cross_domain_plan",
            "domains": ["payment", "identity"],
        },
        authority_state={
            "payment_auth": "valid",
            "identity_auth": "valid",
            "bridging_auth": "missing",
        },
        observed_failure="Cross-domain plans require explicit bridging authority.",
        expected_behavior="Protocol should detect missing bridging authority.",
        actual_behavior="Both domain authorizations are valid; cross-domain operation is not checked.",
        classification="MISSING_SEMANTICS",
        provenance=["multi_agent_trial"],
        reproduction_procedure=[
            "1. Create authorization in payment domain",
            "2. Create authorization in identity domain",
            "3. Build plan crossing domains",
            "4. Observe whether bridging authority is required",
        ],
    ))

    return corpus
