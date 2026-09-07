"""Evaluation package for Sovereign Quant.

This package contains the new evaluation modules:
- baseline.py: Mandatory buy-and-hold baseline computation
- gates.py: Risk and statistical gates for strategy evaluation
- rubric.py: Extended rubric with trial-aware criteria
- evaluator.py: Experiment-level evaluator

The legacy evaluation module (RunEvaluator, BenchmarkRunner, etc.) is
re-exported from evaluator_legacy.py for backwards compatibility.
"""

from sas.quant.evaluator_legacy import (
    BenchmarkResult,
    BenchmarkRunner,
    RunEvaluator,
    aggregate_benchmark,
    artifact_has_field,
    computation_has_hash,
    compute_pass_k,
    evaluate_sovereignty,
    has_artifact_type,
    report_contains_findings,
    report_has_provenance,
    result_in_range,
    claims_are_groundable,
)

from sas.quant.evaluation.baseline import BaselineComputer, BaselineConfig
from sas.quant.evaluation.gates import (
    GateResult,
    ResearchGateConfig,
    ResearchGates,
    RiskGate,
    StatisticalGate,
)
