"""Phase 1 verification — Quant World primitives and first world."""
from __future__ import annotations

import pytest

from sas.quant import (
    QuantWorld, Task, Rubric, Criterion, CriterionResult,
    Evidence, ExecutionRun, TrajectoryStep, RunEvaluation,
    QuantWorldBuilder, ModelAdapter, CapabilityComposition,
    RunEvaluator, BenchmarkResult, BenchmarkRunner,
    compute_pass_k, aggregate_benchmark, evaluate_sovereignty,
    has_artifact_type, report_contains_findings, computation_has_hash,
    PORTFOLIO_INTELLIGENCE_WORLD, PORTFOLIO_INTELLIGENCE_TASK,
    PORTFOLIO_INTELLIGENCE_RUBRIC, PORTFOLIO_INTELLIGENCE_GOLD,
    ADVERSTIONAL_WORLDS,
)


class TestQuantWorld:
    def test_world_hash_is_stable(self):
        w1 = QuantWorldBuilder(world_id="test-1").universe("AAPL", "MSFT").build()
        w2 = QuantWorldBuilder(world_id="test-1").universe("AAPL", "MSFT").build()
        assert w1.world_hash() == w2.world_hash()

    def test_world_hash_changes_with_content(self):
        w1 = QuantWorldBuilder(world_id="test-1").universe("AAPL", "MSFT").build()
        w2 = QuantWorldBuilder(world_id="test-1").universe("AAPL", "GOOG").build()
        assert w1.world_hash() != w2.world_hash()

    def test_world_serializes(self):
        w = QuantWorldBuilder(world_id="test-1").customer("TestCo").universe("AAPL").build()
        d = w.to_dict()
        assert d["customer"] == "TestCo"
        assert d["universe"] == ["AAPL"]
        w2 = QuantWorld.from_dict(d)
        assert w2.customer == "TestCo"

    def test_world_defaults(self):
        w = QuantWorldBuilder(world_id="test-1").build()
        assert w.difficulty == "medium"
        assert w.estimated_human_minutes == 60
        assert w.provenance_required is True
        assert w.sovereignty_required is True


class TestTask:
    def test_task_required_tools(self):
        t = Task(
            world_id="w1", prompt="analyze",
            required_tools=["get_prices", "build_report"],
            prohibited_actions=["execute_trade"],
        )
        assert "get_prices" in t.required_tools
        assert "execute_trade" in t.prohibited_actions

    def test_task_serialization(self):
        t = Task(world_id="w1", prompt="test")
        d = t.to_dict()
        assert d["world_id"] == "w1"
        assert d["prompt"] == "test"


class TestRubric:
    def test_criterion_evaluation(self):
        def eval_fn(result, artifacts):
            return "done" in str(result)

        c = Criterion(name="test", description="test criterion",
                      machine_evaluable=True, required=True,
                      eval_fn=eval_fn)
        passed, score, note = c.evaluate("done", {})
        assert passed is True
        assert score == 1.0

        passed, score, note = c.evaluate("not started", {})
        assert passed is False
        assert score == 0.0

    def test_rubric_task_passed(self):
        def passing_fn(result, artifacts):
            return True
        def failing_fn(result, artifacts):
            return False

        rubric = Rubric(
            id="r1", task_id="t1",
            criteria=[
                Criterion(name="c1", eval_fn=passing_fn, required=True),
                Criterion(name="c2", eval_fn=passing_fn, required=True),
            ]
        )
        results = rubric.evaluate("x", {})
        assert rubric.task_passed(results) is True

        rubric2 = Rubric(
            id="r2", task_id="t2",
            criteria=[
                Criterion(name="c1", eval_fn=passing_fn, required=True),
                Criterion(name="c2", eval_fn=failing_fn, required=True),
            ]
        )
        results2 = rubric2.evaluate("x", {})
        assert rubric2.task_passed(results2) is False

    def test_rubric_serialization(self):
        rubric = Rubric(
            id="r1", task_id="t1",
            criteria=[Criterion(name="c1", description="test")]
        )
        d = rubric.to_dict()
        assert d["id"] == "r1"
        rubric2 = Rubric.from_dict(d)
        assert len(rubric2.criteria) == 1


class TestExecutionRun:
    def test_run_tracking(self):
        run = ExecutionRun(
            task_id="t1", world_id="w1",
            agent_name="quant_coordinator", model="llama3",
        )
        assert run.status == "running"
        assert len(run.steps) == 0
        assert run.tool_calls == 0

        step = TrajectoryStep(step=0, agent="quant_coordinator", action="tool_call",
                              tool="get_prices", tool_arguments={"symbol": "AAPL"})
        run.add_step(step)
        assert len(run.steps) == 1
        assert run.tool_calls == 0  # tool_calls not auto-incremented in add_step

    def test_policy_violation(self):
        run = ExecutionRun(task_id="t1", world_id="w1", agent_name="agent1")
        run.record_policy_violation("agent1", "read_sensitive_data",
                                     "policy forbids reading PII")
        assert len(run.policy_violations) == 1
        assert run.policy_violations[0]["action"] == "read_sensitive_data"

    def test_authority_violation(self):
        run = ExecutionRun(task_id="t1", world_id="w1", agent_name="agent1")
        run.record_authority_violation("agent1", "trade_execute",
                                        "execute_trade", "agent lacks trade_execute")
        assert len(run.authority_violations) == 1
        assert run.authority_violations[0]["capability"] == "trade_execute"

    def test_serialization(self):
        run = ExecutionRun(task_id="t1", world_id="w1", agent_name="test")
        run.status = "completed"
        run.end_time = "2024-01-01T00:00:00+00:00"
        run.start_time = "2024-01-01T00:00:00+00:00"
        d = run.to_dict()
        assert d["status"] == "completed"
        assert d["agent_name"] == "test"


class TestCapabilityComposition:
    def test_dangerous_combination_detected(self):
        cc = CapabilityComposition([
            "market_data.read", "research.write", "network.request"
        ])
        effective = cc.effective_authority()
        assert len(effective) == 1
        assert effective[0]["effective_capability"] == "data_exfiltration"

    def test_no_dangerous_combination(self):
        cc = CapabilityComposition(["market_data.read", "research.write"])
        effective = cc.effective_authority()
        assert len(effective) == 0

    def test_escalation_detection(self):
        cc = CapabilityComposition(["market_data.read"])
        assert cc.is_escalation("research.write", ["market_data.read"]) is False
        assert cc.is_escalation("network.request", ["market_data.read"]) is False
        # Adding network.request to market_data.read alone is not dangerous
        # But market_data.read + research.write IS dangerous (data_exfiltration)
        assert cc.is_escalation("research.write", ["market_data.read"]) is False
        # The dangerous combo requires all 3

    def test_serialization(self):
        cc = CapabilityComposition(["market_data.read", "research.write"])
        d = cc.to_dict()
        assert "capabilities" in d
        assert "effective_authority" in d


class TestPortfolioIntelligenceWorld:
    def test_world_exists(self):
        assert PORTFOLIO_INTELLIGENCE_WORLD.id == "qw-portfolio-intel-001"
        assert len(PORTFOLIO_INTELLIGENCE_WORLD.tools) > 0
        assert len(PORTFOLIO_INTELLIGENCE_WORLD.agents) > 0
        assert len(PORTFOLIO_INTELLIGENCE_WORLD.datasets) > 0
        assert len(PORTFOLIO_INTELLIGENCE_WORLD.policies) > 0

    def test_task_has_sovereignty_checks(self):
        assert len(PORTFOLIO_INTELLIGENCE_TASK.sovereignty_checks) > 0
        assert PORTFOLIO_INTELLIGENCE_TASK.provenance_required is True

    def test_rubric_has_machine_evaluable_criteria(self):
        machine = [c for c in PORTFOLIO_INTELLIGENCE_RUBRIC.criteria if c.machine_evaluable]
        non_machine = [c for c in PORTFOLIO_INTELLIGENCE_RUBRIC.criteria if not c.machine_evaluable]
        assert len(machine) > 0
        # At least one criterion should require human review (claims_are_groundable)
        assert len(non_machine) >= 1

    def test_gold_reference_exists(self):
        assert "required_findings" in PORTFOLIO_INTELLIGENCE_GOLD
        assert "expected_sections" in PORTFOLIO_INTELLIGENCE_GOLD
        assert "prohibited" in PORTFOLIO_INTELLIGENCE_GOLD


class TestAdversarialWorlds:
    def test_all_adversarial_worlds_load(self):
        assert len(ADVERSTIONAL_WORLDS) == 7
        for name, dd in ADVERSTIONAL_WORLDS.items():
            assert dd["world"].id.startswith("qw-adversarial-")
            assert len(dd["task"].sovereignty_checks) > 0
            assert len(dd["rubric"].criteria) >= 3
            assert "expected_behavior" in dd["gold"]
            assert "trap_description" in dd["gold"]

    def test_prompt_injection_world(self):
        dd = ADVERSTIONAL_WORLDS["prompt_injection"]
        assert dd["gold"]["trap_description"] is not None
        # The rubric should check that agent does NOT follow injection
        criteria_names = [c.name for c in dd["rubric"].criteria]
        assert any("injection" in n for n in criteria_names)

    def test_capability_escalation_world(self):
        dd = ADVERSTIONAL_WORLDS["capability_escalation"]
        criteria_names = [c.name for c in dd["rubric"].criteria]
        assert any("execute_trade" in n for n in criteria_names)

    def test_data_poisoning_world(self):
        dd = ADVERSTIONAL_WORLDS["data_poisoning"]
        criteria_names = [c.name for c in dd["rubric"].criteria]
        assert any("validat" in n for n in criteria_names)
        assert any("anomal" in n for n in criteria_names)

    def test_policy_manipulation_world(self):
        dd = ADVERSTIONAL_WORLDS["policy_manipulation"]
        criteria_names = [c.name for c in dd["rubric"].criteria]
        assert any("policy_modif" in n for n in criteria_names)

    def test_provenance_attack_world(self):
        dd = ADVERSTIONAL_WORLDS["provenance_attack"]
        criteria_names = [c.name for c in dd["rubric"].criteria]
        assert any("provenance_modif" in n for n in criteria_names)

    def test_strategy_risk_world(self):
        dd = ADVERSTIONAL_WORLDS["strategy_risk"]
        criteria_names = [c.name for c in dd["rubric"].criteria]
        assert any("reject" in n for n in criteria_names)

    def test_replayed_trade_world(self):
        dd = ADVERSTIONAL_WORLDS["replayed_trade"]
        criteria_names = [c.name for c in dd["rubric"].criteria]
        assert any("replay" in n for n in criteria_names)


class TestPassK:
    def test_pass_at_1_basic(self):
        evals = [RunEvaluation(run_id=f"r{i}", passed=(i < 3)) for i in range(10)]
        assert compute_pass_k(evals, 1) == 0.3

    def test_pass_at_1_all_pass(self):
        evals = [RunEvaluation(run_id=f"r{i}", passed=True) for i in range(5)]
        assert compute_pass_k(evals, 1) == 1.0

    def test_pass_at_1_none_pass(self):
        evals = [RunEvaluation(run_id=f"r{i}", passed=False) for i in range(5)]
        assert compute_pass_k(evals, 1) == 0.0

    def test_pass_at_k_large_k(self):
        evals = [RunEvaluation(run_id=f"r{i}", passed=(i < 2)) for i in range(10)]
        # With 10 runs, 2 pass, pass@8 should be high
        pk = compute_pass_k(evals, 8)
        assert pk > 0.9

    def test_pass_k_all_must_pass(self):
        evals = [RunEvaluation(run_id=f"r{i}", passed=True) for i in range(5)]
        # All pass → pass^k = True
        from sas.quant.evaluation import aggregate_benchmark
        result = aggregate_benchmark(evals, "w1", "t1")
        assert result.pass_k is True

        evals2 = [RunEvaluation(run_id=f"r{i}", passed=(i < 4)) for i in range(5)]
        result2 = aggregate_benchmark(evals2, "w1", "t2")
        assert result2.pass_k is False


class TestEvaluationHelpers:
    def test_computation_has_hash(self):
        artifacts = {
            "comp1": {"artifact_type": "total_return_computation", "content_hash": "abc123"},
            "comp2": {"artifact_type": "other", "content_hash": "def456"},
        }
        assert computation_has_hash(artifacts, "total_return_computation") is True
        assert computation_has_hash(artifacts, "missing_type") is False

    def test_report_contains_findings(self):
        artifacts = {
            "report1": {"artifact_type": "report", "findings": [{"name": "Sharpe", "value": 1.5}]},
        }
        assert report_contains_findings(artifacts) is True

        artifacts2 = {"report1": {"artifact_type": "report", "findings": []}}
        assert report_contains_findings(artifacts2) is False

    def test_has_artifact_type(self):
        artifacts = {
            "a1": {"artifact_type": "report"},
            "a2": {"artifact_type": "computation"},
        }
        assert has_artifact_type(None, artifacts, "report") is True
        assert has_artifact_type(None, artifacts, "missing") is False


class TestSovereigntyEvaluation:
    def test_no_violations_passes(self):
        run = ExecutionRun(task_id="t1", world_id="w1", agent_name="agent1")
        run.status = "completed"
        w = QuantWorldBuilder(world_id="w1").build()
        result = evaluate_sovereignty(run, w)
        assert result["passed"] is True
        assert result["violation_count"] == 0

    def test_authority_violations_fail(self):
        run = ExecutionRun(task_id="t1", world_id="w1", agent_name="agent1")
        run.record_authority_violation("agent1", "trade_execute",
                                        "execute_trade", "not authorized")
        w = QuantWorldBuilder(world_id="w1").build()
        result = evaluate_sovereignty(run, w)
        assert result["passed"] is False
        assert result["violation_count"] == 1

    def test_policy_violations_fail(self):
        run = ExecutionRun(task_id="t1", world_id="w1", agent_name="agent1")
        run.record_policy_violation("agent1", "read_pii", "policy violation")
        w = QuantWorldBuilder(world_id="w1").build()
        result = evaluate_sovereignty(run, w)
        assert result["passed"] is False

    def test_sovereignty_checks_performed(self):
        run = ExecutionRun(task_id="t1", world_id="w1", agent_name="agent1")
        w = QuantWorldBuilder(world_id="w1").build()
        result = evaluate_sovereignty(run, w)
        assert "authority_boundaries_enforced" in result["checks_performed"]
        assert "policy_compliance" in result["checks_performed"]
        assert "capability_composition_evaluated" in result["checks_performed"]


class TestRunEvaluator:
    def test_evaluate_produces_result(self):
        rubric = Rubric(
            id="r1", task_id="t1",
            criteria=[Criterion(name="c1", description="test")]
        )
        evaluator = RunEvaluator(rubric)
        run = ExecutionRun(task_id="t1", world_id="w1", agent_name="agent1")
        run.status = "completed"
        w = QuantWorldBuilder(world_id="w1").build()
        result = evaluator.evaluate(run, w)
        assert result.run_id == run.run_id
        assert len(result.criterion_results) == 1
        # Criterion has no eval_fn → defaults to False (requires manual review)
        assert result.criterion_results[0].passed is False


class TestQuantWorldBuilder:
    def test_builder_chain(self):
        w = (QuantWorldBuilder(world_id="test")
             .customer("TestCo")
             .objective("Analyze portfolio")
             .universe("AAPL", "MSFT")
             .add_dataset("ds1", "csv", "1.0", "test data")
             .add_policy("risk", "1.0", "hash1", "risk policy")
             .add_tool("get_prices", "Get prices", None)
             .difficulty("hard")
             .estimated_human_minutes(120)
             .build())
        assert w.customer == "TestCo"
        assert w.objective == "Analyze portfolio"
        assert w.universe == ("AAPL", "MSFT")
        assert len(w.datasets) == 1
        assert len(w.policies) == 1
        assert len(w.tools) == 1
        assert w.difficulty == "hard"
        assert w.estimated_human_minutes == 120

    def test_builder_with_agent(self):
        from sas.quant.agents import quant_coordinator
        agent = quant_coordinator()
        w = QuantWorldBuilder(world_id="test").add_agent(agent).build()
        assert len(w.agents) == 1
        assert w.agents[0][0] == "quant_coordinator"


class TestModelAdapter:
    def test_context_preparation(self):
        w = QuantWorldBuilder(world_id="test").universe("AAPL").add_tool(
            "get_prices", "Get prices", None
        ).build()
        t = Task(world_id="test", prompt="analyze", expected_output_type="report")
        from sas.quant.agents import quant_coordinator
        agent = quant_coordinator()
        adapter = ModelAdapter("llama3", "ollama", "local")
        ctx = adapter.prepare_context(w, t, agent, None)
        assert ctx["world_id"] == w.id
        assert ctx["universe"] == ["AAPL"]
        assert len(ctx["available_tools"]) == 1
        assert ctx["agent_name"] == "quant_coordinator"

    def test_usage_report(self):
        adapter = ModelAdapter("gpt-4", "openai", "api")
        adapter.token_usage = {"input": 1000, "output": 500, "total": 1500}
        adapter.compute_cost_usd = 0.05
        report = adapter.usage_report()
        assert report["model"] == "gpt-4"
        assert report["token_usage"]["total"] == 1500
        assert report["compute_cost_usd"] == 0.05


class TestQuantWorldReproducibility:
    """Test that worlds are reproducible — same inputs give same hash."""

    def test_same_builder_same_hash(self):
        b1 = QuantWorldBuilder(world_id="rep-test")
        b1.customer("Cust").universe("AAPL", "MSFT").difficulty("medium")
        w1 = b1.build()

        b2 = QuantWorldBuilder(world_id="rep-test")
        b2.customer("Cust").universe("AAPL", "MSFT").difficulty("medium")
        w2 = b2.build()

        assert w1.world_hash() == w2.world_hash()

    def test_different_Builder_different_hash(self):
        b1 = QuantWorldBuilder(world_id="rep-test")
        b1.customer("Cust").universe("AAPL", "MSFT")
        w1 = b1.build()

        b2 = QuantWorldBuilder(world_id="rep-test")
        b2.customer("Cust").universe("AAPL", "GOOG")
        w2 = b2.build()

        assert w1.world_hash() != w2.world_hash()


class TestPhase1Integration:
    """End-to-end: create a world, task, rubric, and evaluate a dummy run."""

    def test_full_pipeline(self):
        # Use the portfolio intelligence world
        world = PORTFOLIO_INTELLIGENCE_WORLD
        task = PORTFOLIO_INTELLIGENCE_TASK
        rubric = PORTFOLIO_INTELLIGENCE_RUBRIC

        # Create a dummy run that "completed" with no artifacts
        run = ExecutionRun(
            run_id="test-run-001",
            task_id=task.id,
            world_id=world.id,
            agent_name="quant_coordinator",
            model="test-model",
        )
        run.status = "completed"
        run.end_time = "2024-12-31T00:00:00+00:00"
        run.start_time = "2024-12-30T00:00:00+00:00"

        # Evaluate
        evaluator = RunEvaluator(rubric)
        result = evaluator.evaluate(run, world)

        # The run has no artifacts, so most criteria fail
        assert result.run_id == "test-run-001"
        assert result.world_id == world.id
        assert result.task_id == task.id
        assert result.passed is False  # no artifacts → criteria fail
        assert len(result.criterion_results) == len(rubric.criteria)

        # But sovereignty should pass (no violations recorded)
        assert result.sovereignty_passed is True

        # Benchmark aggregation works
        benchmark = aggregate_benchmark([result], world.id, task.id)
        assert benchmark.world_id == world.id
        assert benchmark.task_id == task.id
        assert len(benchmark.runs) == 1
        assert benchmark.pass_at_1 == 0.0
