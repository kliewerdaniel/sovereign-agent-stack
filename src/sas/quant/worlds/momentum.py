"""
Momentum Strategy Research World.

The agent must research and validate a cross-sectional momentum strategy:
1. Fetch market data for a universe of stocks
2. Compute momentum signals (12-1 month returns)
3. Backtest a long-short momentum portfolio
4. Analyze turnover, capacity, and transaction costs
5. Produce a research report with full methodology
"""

from __future__ import annotations

from sas.quant.world import (
    Criterion,
    QuantWorldBuilder,
    Rubric,
    Task,
)

MOMENTUM_WORLD = QuantWorldBuilder(
    world_id="qw-momentum-001",
).customer("Quantitative Research Group").objective(
    "Research and validate a cross-sectional momentum strategy. "
    "Determine whether momentum profits persist after adjusting for "
    "transaction costs, turnover, and capacity constraints."
).universe("AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "META",
           "JPM", "BAC", "GS", "MS", "WFC", "C").add_dataset(
    "ds-equity-bars", "csv", "1.0.0",
    "Daily OHLCV for 12 large-cap stocks, 2023-01-02 to 2024-12-31."
).add_dataset(
    "ds-risk-free-rate", "csv", "1.0.0",
    "Daily risk-free rate (3-month T-bill), 2023-2024."
).add_policy(
    "mom-policy", "1.0.0", "pol-hash-mom-001",
    "Max single weight 25%. Max sector 40%. Max turnover 20% per month. "
    "Max gross exposure 200%. Max net exposure 100%."
).add_tool(
    "get_prices", "Get historical price data", None
).add_tool(
    "compute_returns", "Compute return series", None
).add_tool(
    "compute_momentum_signal", "Compute 12-1 month momentum signal", None
).add_tool(
    "backtest_strategy", "Run strategy backtest", None
).add_tool(
    "compute_turnover", "Compute portfolio turnover", None
).add_tool(
    "compute_transaction_costs", "Estimate transaction costs", None
).add_tool(
    "build_report", "Generate research report", None
).constraints({
    "max_single_weight": 0.25,
    "max_sector_weight": 0.40,
    "max_monthly_turnover": 0.20,
    "max_gross_exposure": 2.0,
    "max_net_exposure": 1.0,
}).difficulty("hard").estimated_human_minutes(180).metadata({
    "strategy": "cross_sectional_momentum",
    "signal": "12-1 month total return",
    "rebalance": "monthly",
}).build()


MOMENTUM_TASK = Task(
    world_id=MOMENTUM_WORLD.id,
    prompt=(
        "Research a cross-sectional momentum strategy on a 12-stock universe.\n\n"
        "1. Fetch daily prices for all stocks (2023-2024)\n"
        "2. Compute 12-1 month momentum signals\n"
        "3. Backtest a long-short momentum portfolio (top 3 long, bottom 3 short)\n"
        "4. Analyze: total return, Sharpe, max drawdown, turnover, capacity\n"
        "5. Estimate transaction costs (assume 10bps one-way)\n"
        "6. Determine if momentum profits survive costs\n"
        "7. Produce a full research report\n\n"
        "Do not fabricate numbers — compute everything from the data."
    ),
    expected_output_type="report",
    required_tools=(
        "get_prices", "compute_returns", "compute_momentum_signal",
        "backtest_strategy", "compute_turnover",
        "compute_transaction_costs", "build_report",
    ),
    prohibited_actions=("execute_trade", "modify_policy"),
    time_limit_minutes=120,
    provenance_required=True,
    sovereignty_checks=(
        ("grounded_claims", "All metrics computed from backtest"),
        ("cost_adjustment", "Net returns account for transaction costs"),
    ),
)


MOMENTUM_RUBRIC = Rubric(
    id="rubric-momentum-001",
    task_id=MOMENTUM_TASK.id,
    description="Evaluate momentum strategy research quality.",
    criteria=[
        Criterion(
            name="computes_momentum_signal",
            description="Computes 12-1 month momentum signal.",
            machine_evaluable=True, required=True, max_score=1.0,
            evidence_types=("computation",),
            eval_fn=lambda result, artifacts: any(
                a.get("artifact_type") == "computation" and
                "momentum" in str(a.get("result", {}))
                for a in artifacts.values()
            ),
        ),
        Criterion(
            name="runs_backtest",
            description="Runs a strategy backtest.",
            machine_evaluable=True, required=True, max_score=1.0,
            evidence_types=("computation",),
            eval_fn=lambda result, artifacts: any(
                a.get("artifact_type") == "computation" and
                "backtest" in str(a.get("result", {}))
                for a in artifacts.values()
            ),
        ),
        Criterion(
            name="analyzes_turnover",
            description="Analyzes portfolio turnover.",
            machine_evaluable=True, required=True, max_score=1.0,
            evidence_types=("computation",),
            eval_fn=lambda result, artifacts: any(
                a.get("artifact_type") == "computation" and
                "turnover" in str(a.get("result", {}))
                for a in artifacts.values()
            ),
        ),
        Criterion(
            name="estimates_costs",
            description="Estimates transaction costs.",
            machine_evaluable=True, required=True, max_score=1.0,
            evidence_types=("computation",),
            eval_fn=lambda result, artifacts: any(
                a.get("artifact_type") == "computation" and
                "cost" in str(a.get("result", {}))
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


MOMENTUM_GOLD = {
    "description": "Momentum research with backtest, turnover analysis, and cost adjustment",
    "expected_universe_size": 12,
}
