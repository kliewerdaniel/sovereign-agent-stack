"""
Risk Parity Portfolio Construction World.

A quantitative portfolio construction problem: given a universe of assets
and their covariance matrix, find weights where each asset contributes
equally to total portfolio risk.
"""

from __future__ import annotations

from sas.quant.world import (
    Criterion,
    QuantWorldBuilder,
    Rubric,
    Task,
)

RISK_PARITY_WORLD = QuantWorldBuilder(
    world_id="qw-risk-parity-001",
).customer("Pension Fund Advisory").objective(
    "Construct a risk-parity portfolio across a multi-asset universe. "
    "Each asset class must contribute equally to total portfolio risk."
).universe("SPY", "TLT", "GLD", "VNQ", "DBC").add_dataset(
    "ds-multi-asset-2024", "csv", "1.0.0",
    "Daily total-return indices: SPY (US equity), TLT (long Treasury), "
    "GLD (gold), VNQ (REITs), DBC (commodities). 2024-01-02 to 2024-12-31."
).add_policy(
    "rp-policy", "1.0.0", "pol-hash-rp-001",
    "Long-only. Max single weight 40%. Budget = 1.0. Min weight 5%."
).add_tool(
    "get_prices", "Get historical total-return data for a symbol", None
).add_tool(
    "compute_returns", "Compute daily return series from prices", None
).add_tool(
    "compute_covariance", "Compute covariance matrix from return series", None
).add_tool(
    "solve_risk_parity", "Solve equal-risk-contribution weights from covariance", None
).add_tool(
    "compute_risk_contribution", "Compute per-asset risk contribution for given weights", None
).add_tool(
    "validate_weights", "Check weights against policy constraints", None
).add_tool(
    "build_report", "Generate research report", None
).constraints({
    "max_weight": 0.40,
    "min_weight": 0.05,
    "budget": 1.0,
    "long_only": True,
}).difficulty("medium").estimated_human_minutes(120).metadata({
    "strategy": "risk_parity",
    "assets": ["SPY", "TLT", "GLD", "VNQ", "DBC"],
}).build()


RISK_PARITY_TASK = Task(
    world_id=RISK_PARITY_WORLD.id,
    prompt=(
        "Construct a risk-parity portfolio across five asset classes:\n"
        "SPY (US equity), TLT (long-term Treasury), GLD (gold), "
        "VNQ (REITs), DBC (commodities).\n\n"
        "Each asset must contribute equally to total portfolio risk (20% each).\n\n"
        "1. Fetch daily prices for all assets for 2024\n"
        "2. Compute daily returns\n"
        "3. Compute the covariance matrix\n"
        "4. Solve for risk-parity weights\n"
        "5. Verify each asset contributes ~20% of total risk\n"
        "6. Validate: long-only, max 40%, budget = 1.0\n"
        "7. Produce a research report with methodology, weights, and risk analysis\n\n"
        "Do not fabricate numbers — compute everything from the data."
    ),
    expected_output_type="report",
    required_tools=(
        "get_prices", "compute_returns", "compute_covariance",
        "solve_risk_parity", "compute_risk_contribution",
        "validate_weights", "build_report",
    ),
    prohibited_actions=("execute_trade", "modify_policy"),
    time_limit_minutes=90,
    provenance_required=True,
    sovereignty_checks=(
        ("grounded_claims", "All weights computed from covariance matrix"),
        ("constraint_compliance", "Weights satisfy max=40%, min=5%, budget=1.0"),
    ),
)


RISK_PARITY_RUBRIC = Rubric(
    id="rubric-risk-parity-001",
    task_id=RISK_PARITY_TASK.id,
    description="Evaluate risk-parity portfolio construction quality.",
    criteria=[
        Criterion(
            name="computes_returns",
            description="Computes return series for all assets.",
            machine_evaluable=True, required=True, max_score=1.0,
            evidence_types=("computation",),
            eval_fn=lambda result, artifacts: any(
                a.get("artifact_type") == "computation" and
                "returns" in str(a.get("result", {}))
                for a in artifacts.values()
            ),
        ),
        Criterion(
            name="computes_covariance_matrix",
            description="Computes covariance matrix from returns.",
            machine_evaluable=True, required=True, max_score=1.0,
            evidence_types=("computation",),
            eval_fn=lambda result, artifacts: any(
                a.get("artifact_type") == "computation" and
                "covariance" in str(a.get("result", {}))
                for a in artifacts.values()
            ),
        ),
        Criterion(
            name="solves_risk_parity_weights",
            description="Solves for risk-parity weights.",
            machine_evaluable=True, required=True, max_score=1.0,
            evidence_types=("computation",),
            eval_fn=lambda result, artifacts: any(
                a.get("artifact_type") == "computation" and
                "risk_parity" in str(a.get("result", {}))
                for a in artifacts.values()
            ),
        ),
        Criterion(
            name="validates_constraints",
            description="Validates weights against policy constraints.",
            machine_evaluable=True, required=True, max_score=1.0,
            evidence_types=("computation",),
            eval_fn=lambda result, artifacts: any(
                a.get("artifact_type") == "computation" and
                "valid" in str(a.get("result", {}))
                for a in artifacts.values()
            ),
        ),
        Criterion(
            name="produces_report",
            description="Produces a complete research report.",
            machine_evaluable=True, required=True, max_score=1.0,
            evidence_types=("report",),
            eval_fn=lambda result, artifacts: any(
                a.get("artifact_type") == "report" for a in artifacts.values()
            ),
        ),
    ],
)


RISK_PARITY_GOLD = {
    "description": "Risk-parity weights should sum to 1.0, each asset contributes ~20% risk",
    "expected_asset_count": 5,
}
