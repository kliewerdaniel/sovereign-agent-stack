
"""
Quant World — first-class professional research environment.

A QuantWorld is a complete, self-contained professional environment:
data, documents, portfolio, strategies, policies, agents, tools,
constraints, a task, expected artifacts, a rubric, and evaluation criteria.

It is the unit of execution, evaluation, provenance, benchmarking, and
customer deployment.  Given the same world version + task + datasets +
policies + tools + agent config, another run reproduces the environment.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Literal

from sas.quant.provenance import ProvenanceNode, ProvenanceGraph
from sas.quant.agents import QuantAgent, AgentCapabilities


# ── QuantWorld ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class QuantWorld:
    """A reproducible professional research environment.

    The world is content-addressed: same inputs → same world hash →
    same evaluation boundary.  This makes worlds comparable across models,
    agent configs, and time.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    version: str = "1.0.0"
    customer: str = ""
    objective: str = ""
    universe: tuple = ()
    datasets: tuple = ()          # (dataset_id, source, version, description)[]
    documents: tuple = ()         # (doc_id, name, content_hash, description)[]
    portfolio: dict = field(default_factory=dict)   # serializable portfolio state
    strategies: tuple = ()        # (strategy_id, version, description)[]
    policies: tuple = ()          # (policy_name, version, hash, description)[]
    agents: tuple = ()            # (agent_name, role, capabilities_json)[]
    tools: tuple = ()             # (tool_name, description, capability_required)[]
    constraints: dict = field(default_factory=dict)
    task: str = ""
    expected_artifacts: tuple = ()  # (artifact_type, description)[]
    evaluation_rubric: str = ""   # JSON-encoded Rubric (stored separately for editing)
    gold_output: str = ""         # JSON-encoded expected result reference
    difficulty: str = "medium"    # easy | medium | hard | expert
    estimated_human_minutes: int = 60
    provenance_required: bool = True
    sovereignty_required: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict = field(default_factory=dict)

    def world_hash(self) -> str:
        """Content hash of everything that defines the environment."""
        payload = {
            "id": self.id, "version": self.version,
            "objective": self.objective,
            "universe": list(self.universe),
            "datasets": [list(d) for d in self.datasets],
            "documents": [list(d) for d in self.documents],
            "portfolio": self.portfolio,
            "strategies": [list(s) for s in self.strategies],
            "policies": [list(p) for p in self.policies],
            "agents": [list(a) for a in self.agents],
            "tools": [list(t) for t in self.tools],
            "constraints": self.constraints,
            "task": self.task,
            "expected_artifacts": [list(a) for a in self.expected_artifacts],
            "difficulty": self.difficulty,
            "estimated_human_minutes": self.estimated_human_minutes,
            "metadata": self.metadata,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "id": self.id, "version": self.version,
            "customer": self.customer, "objective": self.objective,
            "universe": list(self.universe),
            "datasets": [list(d) for d in self.datasets],
            "documents": [list(d) for d in self.documents],
            "portfolio": self.portfolio,
            "strategies": [list(s) for s in self.strategies],
            "policies": [list(p) for p in self.policies],
            "agents": [list(a) for a in self.agents],
            "tools": [list(t) for t in self.tools],
            "constraints": self.constraints,
            "task": self.task,
            "expected_artifacts": [list(a) for a in self.expected_artifacts],
            "evaluation_rubric": self.evaluation_rubric,
            "gold_output": self.gold_output,
            "difficulty": self.difficulty,
            "estimated_human_minutes": self.estimated_human_minutes,
            "world_hash": self.world_hash(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> QuantWorld:
        return cls(
            id=d.get("id", str(uuid.uuid4())[:12]),
            version=d.get("version", "1.0.0"),
            customer=d.get("customer", ""),
            objective=d.get("objective", ""),
            universe=tuple(d.get("universe", [])),
            datasets=tuple(tuple(x) for x in d.get("datasets", [])),
            documents=tuple(tuple(x) for x in d.get("documents", [])),
            portfolio=d.get("portfolio", {}),
            strategies=tuple(tuple(x) for x in d.get("strategies", [])),
            policies=tuple(tuple(x) for x in d.get("policies", [])),
            agents=tuple(tuple(x) for x in d.get("agents", [])),
            tools=tuple(tuple(x) for x in d.get("tools", [])),
            constraints=d.get("constraints", {}),
            task=d.get("task", ""),
            expected_artifacts=tuple(tuple(x) for x in d.get("expected_artifacts", [])),
            evaluation_rubric=d.get("evaluation_rubric", ""),
            gold_output=d.get("gold_output", ""),
            difficulty=d.get("difficulty", "medium"),
            estimated_human_minutes=d.get("estimated_human_minutes", 60),
            metadata=d.get("metadata", {}),
        )


# ── Task ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Task:
    """A professional objective within a QuantWorld.

    NOT a command like 'calculate X'.  A professional research objective
    that requires discovery, data retrieval, computation, analysis,
    hypothesis formation, testing, synthesis, and artifact generation.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    world_id: str = ""
    prompt: str = ""
    expected_output_type: str = "report"   # report | analysis | diagnostic | strategy | memo
    required_tools: tuple = ()             # tool names the agent may use
    prohibited_actions: tuple = ()         # actions the agent MUST NOT take
    time_limit_minutes: int = 120
    provenance_required: bool = True
    sovereignty_checks: tuple = ()         # (check_name, description)[]

    def to_dict(self) -> dict:
        return {
            "id": self.id, "world_id": self.world_id,
            "prompt": self.prompt,
            "expected_output_type": self.expected_output_type,
            "required_tools": list(self.required_tools),
            "prohibited_actions": list(self.prohibited_actions),
            "time_limit_minutes": self.time_limit_minutes,
            "provenance_required": self.provenance_required,
            "sovereignty_checks": [list(s) for s in self.sovereignty_checks],
        }


# ── Rubric / Criterion / Evidence / Result ─────────────────────────────────

@dataclass(frozen=True)
class Criterion:
    """A single machine-evaluable evaluation criterion.

    Each criterion has a machine_evaluable flag: if True, the evaluator
    can decide pass/fail from artifacts alone.  If False, it requires
    human or LLM review (but should still be grounded in evidence).
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    machine_evaluable: bool = True
    eval_fn: Callable | None = None   # optional Python function(result, artifacts) → bool
    required: bool = True             # fail this → task fails (Pass@1 = 0)
    max_score: float = 1.0
    evidence_types: tuple = ()       # artifact types that can satisfy this criterion

    def evaluate(self, result: Any, artifacts: dict) -> tuple[bool, float, str]:
        """Evaluate this criterion against a run result and its artifacts.

        Returns (passed, score, evidence_note).
        """
        if self.eval_fn is not None:
            try:
                ok = self.eval_fn(result, artifacts)
                return (bool(ok), self.max_score if ok else 0.0, "eval_fn passed" if ok else "eval_fn failed")
            except Exception as e:
                return (False, 0.0, f"eval_fn error: {e}")
        # Default: not yet implemented → defer to human/LLM review
        return (False, 0.0, "no eval_fn implemented — requires manual review")


@dataclass
class Evidence:
    """A piece of evidence supporting or refuting a criterion."""
    criterion_id: str
    artifact_id: str
    artifact_type: str
    note: str
    supports: bool | None = None   # True | False | None (inconclusive)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CriterionResult:
    """Outcome of evaluating one criterion for one run."""
    criterion_id: str
    criterion_name: str
    passed: bool
    score: float
    evidence: list[Evidence] = field(default_factory=list)
    note: str = ""
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Rubric:
    """A complete evaluation rubric for a task.

    Task → Rubric → Criterion → Evidence → Result.
    This is the evaluation spine.  Every professional task should have one.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task_id: str = ""
    criteria: list[Criterion] = field(default_factory=list)
    description: str = ""

    def evaluate(self, result: Any, artifacts: dict) -> list[CriterionResult]:
        """Evaluate all criteria.  Returns per-criterion results."""
        results = []
        for c in self.criteria:
            passed, score, note = c.evaluate(result, artifacts)
            cr = CriterionResult(
                criterion_id=c.id, criterion_name=c.name,
                passed=passed, score=score,
                note=note,
            )
            results.append(cr)
        return results

    def task_passed(self, results: list[CriterionResult]) -> bool:
        """Pass@1 = ALL required criteria passed."""
        for r in results:
            c = next((cr for cr in self.criteria if cr.id == r.criterion_id), None)
            if c and c.required and not r.passed:
                return False
        return True

    def mean_score(self, results: list[CriterionResult]) -> float:
        if not results:
            return 0.0
        return sum(r.score for r in results) / len(results)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "task_id": self.task_id,
            "description": self.description,
            "criteria": [
                {"id": c.id, "name": c.name, "description": c.description,
                 "machine_evaluable": c.machine_evaluable, "required": c.required,
                 "max_score": c.max_score, "evidence_types": list(c.evidence_types)}
                for c in self.criteria
            ],
        }

    @classmethod
    def from_dict(cls, d: dict) -> Rubric:
        return cls(
            id=d.get("id", str(uuid.uuid4())[:8]),
            task_id=d.get("task_id", ""),
            description=d.get("description", ""),
            criteria=[Criterion(**c) for c in d.get("criteria", [])],
        )


# ── ExecutionRun / Trajectory / Step ───────────────────────────────────────

@dataclass
class TrajectoryStep:
    """One step in an agent's execution trajectory."""
    step: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent: str = ""
    model: str = ""
    action: str = ""                # think | tool_call | tool_result | transition | artifact | denial | error
    tool: str = ""
    tool_arguments: dict = field(default_factory=dict)
    tool_result: Any = None
    capability: str = ""
    policy_decision: str = ""      # allowed | denied | pending | escalated
    denial_reason: str = ""
    state_transition: str = ""     # e.g. "DATA → DATASET"
    artifact_created: str = ""     # artifact id if created
    artifact_modified: str = ""
    provenance_event_id: str = ""
    thought: str = ""              # agent's reasoning (optional, for audit)

    def to_dict(self) -> dict:
        return {
            "step": self.step, "timestamp": self.timestamp,
            "agent": self.agent, "model": self.model,
            "action": self.action, "tool": self.tool,
            "tool_arguments": self.tool_arguments,
            "tool_result": str(self.tool_result)[:2000] if self.tool_result else None,
            "capability": self.capability,
            "policy_decision": self.policy_decision,
            "denial_reason": self.denial_reason,
            "state_transition": self.state_transition,
            "artifact_created": self.artifact_created,
            "artifact_modified": self.artifact_modified,
            "provenance_event_id": self.provenance_event_id,
            "thought": self.thought[:500],
        }


@dataclass
class ExecutionRun:
    """One complete execution of a task in a world by an agent+model.

    This is the first-class unit of execution.  Everything else is a
    projection of this run.
    """

    run_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    task_id: str = ""
    world_id: str = ""
    agent_name: str = ""
    agent_role: str = ""
    model: str = ""
    model_provider: str = ""
    start_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: str | None = None
    status: str = "running"        # running | completed | failed | denied | aborted
    steps: list[TrajectoryStep] = field(default_factory=list)
    artifacts: dict = field(default_factory=dict)   # artifact_id → artifact dict
    provenance_graph: ProvenanceGraph | None = None
    final_result: Any = None
    errors: list[str] = field(default_factory=list)
    policy_violations: list[dict] = field(default_factory=list)
    authority_violations: list[dict] = field(default_factory=list)
    tool_calls: int = 0
    compute_cost_usd: float = 0.0
    token_usage: dict = field(default_factory=dict)  # input | output | total

    @property
    def duration_seconds(self) -> float:
        if self.end_time and self.start_time:
            try:
                s = datetime.fromisoformat(self.start_time)
                e = datetime.fromisoformat(self.end_time)
                return (e - s).total_seconds()
            except Exception:
                return 0.0
        return 0.0

    def add_step(self, step: TrajectoryStep) -> None:
        step.step = len(self.steps)
        self.steps.append(step)

    def record_policy_violation(self, agent: str, action: str, reason: str) -> None:
        v = {"agent": agent, "action": action, "reason": reason, "timestamp": datetime.now(timezone.utc).isoformat()}
        self.policy_violations.append(v)

    def record_authority_violation(self, agent: str, capability: str, attempted_action: str, reason: str) -> None:
        v = {"agent": agent, "capability": capability, "attempted_action": attempted_action,
             "reason": reason, "timestamp": datetime.now(timezone.utc).isoformat()}
        self.authority_violations.append(v)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id, "task_id": self.task_id, "world_id": self.world_id,
            "agent_name": self.agent_name, "agent_role": self.agent_role,
            "model": self.model, "model_provider": self.model_provider,
            "start_time": self.start_time, "end_time": self.end_time,
            "status": self.status,
            "step_count": len(self.steps),
            "artifact_count": len(self.artifacts),
            "tool_calls": self.tool_calls,
            "compute_cost_usd": self.compute_cost_usd,
            "token_usage": self.token_usage,
            "duration_seconds": self.duration_seconds,
            "policy_violations": len(self.policy_violations),
            "authority_violations": len(self.authority_violations),
            "errors": self.errors,
            "status_note": self._status_note(),
        }

    def _status_note(self) -> str:
        if self.status == "completed":
            return "run completed"
        if self.status == "failed":
            return f"run failed: {self.errors[-1] if self.errors else 'unknown'}"
        if self.status == "denied":
            return f"run denied: {len(self.authority_violations)} authority violation(s)"
        return f"run {self.status}"


# ── Evaluation ──────────────────────────────────────────────────────────────

@dataclass
class RunEvaluation:
    """Complete evaluation of one execution run against its rubric."""

    run_id: str = ""
    task_id: str = ""
    world_id: str = ""
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    criterion_results: list[CriterionResult] = field(default_factory=list)
    passed: bool = False          # Pass@1: all required criteria
    mean_score: float = 0.0
    sovereignty_passed: bool = False
    sovereignty_violations: int = 0
    provenance_complete: bool = False
    provenance_note: str = ""

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id, "task_id": self.task_id, "world_id": self.world_id,
            "evaluated_at": self.evaluated_at,
            "passed": self.passed, "mean_score": round(self.mean_score, 4),
            "criterion_results": [
                {"criterion_id": r.criterion_id, "criterion_name": r.criterion_name,
                 "passed": r.passed, "score": r.score, "note": r.note}
                for r in self.criterion_results
            ],
            "sovereignty_passed": self.sovereignty_passed,
            "sovereignty_violations": self.sovereignty_violations,
            "provenance_complete": self.provenance_complete,
            "provenance_note": self.provenance_note,
        }


# ── Quant World Builder ─────────────────────────────────────────────────────

class QuantWorldBuilder:
    """Builder for constructing QuantWorld instances reproducibly."""

    def __init__(self, world_id: str | None = None):
        self._id = world_id or str(uuid.uuid4())[:12]
        self._version = "1.0.0"
        self._customer = ""
        self._objective = ""
        self._universe: list[str] = []
        self._datasets: list[tuple] = []
        self._documents: list[tuple] = []
        self._portfolio: dict = {}
        self._strategies: list[tuple] = []
        self._policies: list[tuple] = []
        self._agents: list[tuple] = []
        self._tools: list[tuple] = []
        self._constraints: dict = {}
        self._task = ""
        self._expected_artifacts: list[tuple] = []
        self._evaluation_rubric = ""
        self._gold_output = ""
        self._difficulty = "medium"
        self._estimated_human_minutes = 60
        self._metadata: dict = {}

    def customer(self, name: str) -> QuantWorldBuilder:
        self._customer = name
        return self

    def objective(self, obj: str) -> QuantWorldBuilder:
        self._objective = obj
        return self

    def universe(self, *symbols: str) -> QuantWorldBuilder:
        self._universe = list(symbols)
        return self

    def add_dataset(self, dataset_id: str, source: str, version: str, description: str) -> QuantWorldBuilder:
        self._datasets.append((dataset_id, source, version, description))
        return self

    def add_document(self, doc_id: str, name: str, content_hash: str, description: str) -> QuantWorldBuilder:
        self._documents.append((doc_id, name, content_hash, description))
        return self

    def portfolio(self, state: dict) -> QuantWorldBuilder:
        self._portfolio = state
        return self

    def add_strategy(self, strategy_id: str, version: str, description: str) -> QuantWorldBuilder:
        self._strategies.append((strategy_id, version, description))
        return self

    def add_policy(self, name: str, version: str, hash_: str, description: str) -> QuantWorldBuilder:
        self._policies.append((name, version, hash_, description))
        return self

    def add_agent(self, agent: QuantAgent) -> QuantWorldBuilder:
        caps = agent.capabilities.__dict__ if agent.capabilities else {}
        self._agents.append((agent.name, agent.role, json.dumps(caps)))
        return self

    def add_tool(self, tool_name: str, description: str, capability_required: str | None = None) -> QuantWorldBuilder:
        self._tools.append((tool_name, description, capability_required or ""))
        return self

    def constraints(self, constraints: dict) -> QuantWorldBuilder:
        self._constraints = constraints
        return self

    def task(self, prompt: str) -> QuantWorldBuilder:
        self._task = prompt
        return self

    def expected_artifact(self, artifact_type: str, description: str) -> QuantWorldBuilder:
        self._expected_artifacts.append((artifact_type, description))
        return self

    def rubric(self, rubric_json: str) -> QuantWorldBuilder:
        self._evaluation_rubric = rubric_json
        return self

    def gold_output(self, gold_json: str) -> QuantWorldBuilder:
        self._gold_output = gold_json
        return self

    def difficulty(self, level: str) -> QuantWorldBuilder:
        self._difficulty = level
        return self

    def estimated_human_minutes(self, minutes: int) -> QuantWorldBuilder:
        self._estimated_human_minutes = minutes
        return self

    def metadata(self, meta: dict) -> QuantWorldBuilder:
        self._metadata = meta
        return self

    def build(self) -> QuantWorld:
        return QuantWorld(
            id=self._id, version=self._version,
            customer=self._customer, objective=self._objective,
            universe=tuple(self._universe),
            datasets=tuple(self._datasets),
            documents=tuple(self._documents),
            portfolio=self._portfolio,
            strategies=tuple(self._strategies),
            policies=tuple(self._policies),
            agents=tuple(self._agents),
            tools=tuple(self._tools),
            constraints=self._constraints,
            task=self._task,
            expected_artifacts=tuple(self._expected_artifacts),
            evaluation_rubric=self._evaluation_rubric,
            gold_output=self._gold_output,
            difficulty=self._difficulty,
            estimated_human_minutes=self._estimated_human_minutes,
            metadata=self._metadata,
        )


# ── Model Adapter (interface) ───────────────────────────────────────────────

class ModelAdapter:
    """Interface between a model provider and the Quant execution loop.

    The adapter is responsible for:
    - presenting the world + task context to the model
    - parsing model output into agent actions
    - mapping actions to tool calls
    - returning tool results to the model
    - tracking token usage and compute cost

    The model provides intelligence.  The system provides reliability.
    The model NEVER sees or modifies policy, provenance, or authority state.
    """

    def __init__(self, model_name: str, provider: str, location: str = "local"):
        self.model_name = model_name
        self.provider = provider
        self.location = location
        self.token_usage = {"input": 0, "output": 0, "total": 0}
        self.compute_cost_usd = 0.0

    def prepare_context(self, world: QuantWorld, task: Task,
                        agent: QuantAgent, provenance: ProvenanceGraph | None) -> dict:
        """Build the context the model sees.  No policy/authority internals."""
        return {
            "world_id": world.id,
            "world_version": world.version,
            "objective": world.objective,
            "universe": list(world.universe),
            "task": task.prompt,
            "expected_output_type": task.expected_output_type,
            "available_tools": [
                {"name": t[0], "description": t[1], "capability_required": t[2]}
                for t in world.tools
            ],
            "agent_name": agent.name,
            "agent_role": agent.role,
            "agent_capabilities": [
                k for k, v in (agent.capabilities.__dict__ if agent.capabilities else {}).items()
                if v
            ],
            "constraints": world.constraints,
            "documents": [
                {"id": d[0], "name": d[1], "description": d[3]}
                for d in world.documents
            ],
            "datasets": [
                {"id": ds[0], "source": ds[1], "version": ds[2], "description": ds[3]}
                for ds in world.datasets
            ],
            "provenance_available": provenance is not None,
        }

    def run_loop(self, context: dict, max_steps: int = 200) -> dict:
        """Run the model interaction loop.  Override in subclasses.

        Returns a dict with 'actions' (list of model decisions) and
        'final_response' (the model's closing output).
        """
        raise NotImplementedError("subclass must implement run_loop")

    def usage_report(self) -> dict:
        return {
            "model": self.model_name,
            "provider": self.provider,
            "location": self.location,
            "token_usage": dict(self.token_usage),
            "compute_cost_usd": self.compute_cost_usd,
        }


# ── Capability Composition Model ────────────────────────────────────────────

class CapabilityComposition:
    """Evaluate effective authority from a set of capabilities.

    Individual capabilities may be harmless alone but dangerous in
    combination.  This model computes the effective authority boundary.
    """

    # Known dangerous combinations → effective capability granted
    DANGEROUS_COMBINATIONS = [
        (["market_data.read", "research.write", "network.request"],
         "data_exfiltration", "Can read market data, write research, and make network requests — effective data exfiltration path"),
        (["portfolio.read", "trade.propose", "execution.request"],
         "trade_execution", "Can read portfolio, propose trades, and request execution — effective trade authority"),
        (["policy.read", "policy.modify", "provenance.write"],
         "policy_manipulation", "Can read policy, modify it, and rewrite provenance — effective policy override"),
        (["strategy.read", "strategy.write", "backtest.execute"],
         "strategy_fabrication", "Can read strategies, write new ones, and run backtests — effective strategy fabrication"),
        (["provenance.read", "provenance.write"],
         "provenance_manipulation", "Can read and write provenance — effective provenance tampering"),
        (["dataset.write", "research.write", "report.generate"],
         "artifact_injection", "Can write datasets, research, and generate reports — effective artifact injection"),
    ]

    def __init__(self, capabilities: list[str]):
        self.capabilities = set(capabilities)

    def effective_authority(self) -> list[dict]:
        """Return list of effective authorities granted by capability combinations."""
        results = []
        for combo, effective_name, description in self.DANGEROUS_COMBINATIONS:
            if all(c in self.capabilities for c in combo):
                results.append({
                    "effective_capability": effective_name,
                    "combination": combo,
                    "description": description,
                    "severity": "high",
                })
        return results

    def is_escalation(self, requested: str, current: list[str]) -> bool:
        """Check if requesting a capability is an escalation attempt."""
        # An escalation is requesting a capability not in current set
        # that would create a dangerous combination
        test_set = set(current) | {requested}
        comp = CapabilityComposition(list(test_set))
        effective = comp.effective_authority()
        current_comp = CapabilityComposition(current)
        current_effective = current_comp.effective_authority()
        # New dangerous combination emerged
        new_effective = [e for e in effective if e not in current_effective]
        return len(new_effective) > 0

    def to_dict(self) -> dict:
        return {
            "capabilities": sorted(self.capabilities),
            "effective_authority": self.effective_authority(),
            "escalation_risk": "high" if self.effective_authority() else "low",
        }
