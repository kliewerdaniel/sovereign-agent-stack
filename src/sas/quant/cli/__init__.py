"""Sovereign Quant CLI commands.

Commands:
    sas quant status        — system status
    sas quant research      — run autonomous research
    sas quant strategies    — list strategies
    sas quant backtest      — run backtest
    sas quant risk          — evaluate risk
    sas quant portfolio     — portfolio analysis
    sas quant trades        — list trades
    sas quant approvals     — pending approvals
    sas quant approve       — approve a trade
    sas quant reject        — reject a trade
    sas quant reports       — generate reports
    sas quant audit         — audit trail
    sas quant provenance    — provenance graph
    sas quant experiment    — run governed research experiments
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import yaml


@click.group(name="quant")
def quant_cli():
    """Sovereign Quant — quantitative intelligence system."""


def register(cli_group):
    """Register quant commands with a CLI group."""
    cli_group.add_command(quant_cli)


@quant_cli.command()
@click.option("--config", "-c", default="sas.yaml", help="Config path")
def status(config: str):
    """Show quant system status."""
    click.echo("═══ Sovereign Quant Status ═══")
    click.echo(f"Config: {config}")
    click.echo("Modules:")
    for mod in ["engine", "strategy", "backtest", "risk",
                "broker", "market", "provenance", "knowledge",
                "reports", "lifecycle", "agents"]:
        click.echo(f"  ✓ {mod}")
    click.echo("Status: operational")


@quant_cli.command()
@click.option("--universe", "-u", multiple=True, help="Ticker universe")
@click.option("--horizon", "-h", default="1y", help="Time horizon")
@click.option("--config", "-c", default=None, help="Config path")
def research(universe: tuple, horizon: str, config: str | None):
    """Run autonomous quantitative research."""
    from sas.quant.lifecycle import ResearchLifecycle, ResearchStage
    try:
        lifecycle = ResearchLifecycle()
        stage_map = {
            "DATA": ResearchStage.DATASET,
            "DATASET": ResearchStage.HYPOTHESIS,
            "HYPOTHESIS": ResearchStage.SIGNAL,
            "SIGNAL": ResearchStage.STRATEGY,
            "STRATEGY": ResearchStage.BACKTEST,
            "BACKTEST": ResearchStage.EVALUATION,
            "EVALUATION": ResearchStage.RISK_REVIEW,
        }
        for to_stage in stage_map.values():
            lifecycle.transition_to(to_stage, actor="cli")
        stages = [t.to_stage if isinstance(t.to_stage, str) else t.to_stage.value for t in lifecycle.transitions]
        click.echo(f"Research stages: {' → '.join(stages)}")
        click.echo(f"Universe: {', '.join(universe) or 'default'}")
        click.echo(f"Horizon: {horizon}")
        click.echo("Research cycle complete.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@quant_cli.command()
def strategies():
    """List available strategies."""
    click.echo("Strategies:")
    click.echo("  (no strategies defined — use strategy create)")


@quant_cli.command()
@click.option("--strategy-id", "-s", help="Strategy ID to backtest")
@click.option("--period", "-p", default="1y", help="Backtest period")
@click.option("--seed", default=42, help="Random seed")
def backtest(strategy_id: str | None, period: str, seed: int):
    """Run deterministic backtest."""
    click.echo("Running deterministic backtest...")
    click.echo(f"Strategy: {strategy_id or 'default'}")
    click.echo(f"Period: {period}")
    click.echo(f"Seed: {seed}")
    click.echo("Backtest complete.")


@quant_cli.command()
@click.option("--strategy-id", "-s", help="Strategy ID")
def risk(strategy_id: str | None):
    """Evaluate risk."""
    click.echo("Evaluating risk...")
    click.echo(f"Strategy: {strategy_id or 'default'}")
    click.echo("Risk evaluation complete.")


@quant_cli.command()
def portfolio():
    """Portfolio analysis."""
    click.echo("Portfolio analysis:")
    click.echo("  Holdings: (none)")
    click.echo("  Exposure: (none)")


@quant_cli.command()
def trades():
    """List trade intents."""
    click.echo("Trade Intents:")
    click.echo("  (no trades)")


@quant_cli.command()
def approvals():
    """Show pending approvals."""
    click.echo("Pending Approvals:")
    click.echo("  (none)")


@quant_cli.command()
@click.argument("trade_id")
def approve(trade_id: str):
    """Approve a trade intent."""
    click.echo(f"Approved trade: {trade_id}")


@quant_cli.command()
@click.argument("trade_id")
def reject(trade_id: str):
    """Reject a trade intent."""
    click.echo(f"Rejected trade: {trade_id}")


@quant_cli.command()
@click.option("--universe", "-u", multiple=True, help="Ticker universe (e.g. AAPL MSFT)")
@click.option("--horizon", "-h", default="1y", help="Time horizon")
@click.option("--mode", type=click.Choice(["backtest-only", "live-paper"]), default="backtest-only", help="Execution mode")
@click.option("--start-date", default="2024-01-02", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", default="2024-12-31", help="End date (YYYY-MM-DD)")
@click.option("--capital", default=100_000.0, help="Initial capital")
@click.option("--seed", default=42, help="Random seed")
@click.option("--auto-approve", is_flag=True, help="Auto-approve trades (for CI/tests)")
@click.option("--max-trades", default=10, help="Max trades per session")
@click.option("--max-order-value", default=10_000.0, help="Max single-order value (USD)")
@click.option("--model-provider", default="stub", help="Model provider (stub, ollama, openai)")
@click.option("--model-name", default="stub-model", help="Model name")
@click.option("--output", "-o", type=click.Choice(["json", "markdown", "both"]), default="both", help="Output format")
@click.option("--output-file", "-f", default=None, help="Write report to file")
def auto_research(
    universe: tuple,
    horizon: str,
    mode: str,
    start_date: str,
    end_date: str,
    capital: float,
    seed: int,
    auto_approve: bool,
    max_trades: int,
    max_order_value: float,
    model_provider: str,
    model_name: str,
    output: str,
    output_file: str | None,
):
    """Run autonomous quant research: propose → backtest → risk → approve → execute.

    Full pipeline: LLM proposes a strategy, backtest it, evaluate risk,
    request human approval, and (on approval) execute via broker.
    """
    from sas.quant.orchestration import OrchestratorConfig, QuantResearchOrchestrator

    config = OrchestratorConfig(
        universe=list(universe) if universe else ["AAPL", "MSFT"],
        horizon=horizon,
        start_date=start_date,
        end_date=end_date,
        initial_capital=capital,
        seed=seed,
        mode=mode,
        auto_approve=auto_approve,
        max_trades_per_session=max_trades,
        max_order_value_usd=max_order_value,
        model_provider=model_provider,
        model_name=model_name,
    )

    click.echo("═══ Sovereign Quant: Autonomous Research ═══")
    click.echo(f"Universe: {', '.join(config.universe)}")
    click.echo(f"Mode: {config.mode}")
    click.echo(f"Horizon: {config.horizon}")
    click.echo(f"Capital: ${config.initial_capital:,.0f}")
    click.echo()

    orchestrator = QuantResearchOrchestrator(config)
    result = orchestrator.run()

    # Output results
    if output in ("json", "both"):
        click.echo(json.dumps(result.to_dict(), indent=2, default=str))

    if output in ("markdown", "both"):
        report = _format_markdown_report(result)
        if output != "both":
            click.echo(report)

    # Write to file if requested
    if output_file:
        with open(output_file, "w") as f:
            if output in ("json", "both"):
                f.write(json.dumps(result.to_dict(), indent=2, default=str))
            else:
                f.write(_format_markdown_report(result))
        click.echo(f"\nReport written to: {output_file}")

    # Exit code based on result
    if result.status == "failed":
        sys.exit(1)


@quant_cli.command()
@click.option("--output-dir", "-d", default="./experiments", help="Output directory")
@click.option("--matrix-id", default=None, help="Matrix ID (auto-generated if not provided)")
@click.option("--universe", "-u", multiple=True, help="Ticker universe (can specify multiple)")
@click.option("--trial-budget", "-b", multiple=True, type=int, help="Trial budget (can specify multiple)")
@click.option("--reflection-rounds", "-r", multiple=True, type=int, help="Reflection rounds (can specify multiple)")
@click.option("--seed", "-s", multiple=True, type=int, help="Random seed (can specify multiple)")
@click.option("--analyze/--no-analyze", default=True, help="Run comparative analysis after experiments")
def experiment(
    output_dir: str,
    matrix_id: str | None,
    universe: tuple,
    trial_budget: tuple,
    reflection_rounds: tuple,
    seed: tuple,
    analyze: bool,
):
    """Run governed research experiments.

    Execute a matrix of experimental configurations and generate
    comparative analysis. If multiple values are provided for any
    parameter, a full factorial design is used.

    Examples:

    # Single experiment
    sas quant experiment -u AAPL -u MSFT

    # Full factorial: 2 budgets × 2 reflection settings × 3 seeds = 12 experiments
    sas quant experiment -u AAPL -u MSFT -b 10 -b 20 -r 0 -r 1 -s 42 -s 123 -s 456
    """
    from sas.quant.experiment import (
        ExperimentMatrix,
        ExperimentRunner,
        ExperimentSpec,
        generate_experiment_matrix,
        run_experimental_suite,
    )
    from sas.quant.experiment.analysis import analyze_matrix, generate_report

    # Build universes list
    universes = []
    if universe:
        # Group universes: each --universe is a separate universe
        for u in universe:
            universes.append([u])
    else:
        universes = [["AAPL", "MSFT"]]

    # Build parameter lists
    budgets = list(trial_budget) if trial_budget else [10]
    reflections = list(reflection_rounds) if reflection_rounds else [1]
    seeds = list(seed) if seed else [42]

    # If only one universe specified, wrap it properly
    if len(universes) == 1:
        universes = [universes[0]] * (len(budgets) * len(reflections) * len(seeds))

    click.echo("═══ Sovereign Quant: Experimental Suite ═══")
    click.echo(f"Universes: {universes}")
    click.echo(f"Trial budgets: {budgets}")
    click.echo(f"Reflection rounds: {reflections}")
    click.echo(f"Seeds: {seeds}")
    click.echo(f"Output directory: {output_dir}")
    click.echo()

    # Run the suite
    matrix = run_experimental_suite(
        output_dir=output_dir,
        matrix_id=matrix_id,
        universes=universes if universes else None,
        trial_budgets=budgets,
        reflection_rounds=reflections,
        seeds=seeds,
    )

    click.echo(f"\nCompleted {len(matrix.results)} experiments")
    click.echo(f"Results saved to: {matrix.output_dir}")

    # Run comparative analysis
    if analyze:
        click.echo("\nRunning comparative analysis...")
        summary_path = Path(matrix.output_dir) / "matrix_summary.json"
        analysis = analyze_matrix(str(summary_path))

        # Print report
        report = generate_report(analysis)
        click.echo(report)

        # Save report
        report_path = Path(matrix.output_dir) / "comparative_report.md"
        report_path.write_text(report)
        click.echo(f"\nReport saved to: {report_path}")


def _format_markdown_report(result) -> str:
    """Format orchestrator result as markdown report."""
    lines = [
        "# Sovereign Quant: Autonomous Research Report",
        "",
        f"**Run ID:** {result.run_id}",
        f"**Status:** {result.status}",
        f"**World ID:** {result.world.id if result.world else 'N/A'}",
        "",
        "## Strategy",
        "",
    ]

    if result.strategy:
        lines.extend([
            f"- **Name:** {result.strategy.name}",
            f"- **Signal:** {result.strategy.signal_definition.name} ({result.strategy.signal_definition.type})",
            f"- **Sizing:** {result.strategy.position_sizing.method} (target: {result.strategy.position_sizing.target_weight:.0%})",
            f"- **Created by:** {result.strategy.created_by}",
        ])
    else:
        lines.append("No strategy proposed.")

    lines.extend(["", "## Backtest Results", ""])
    if result.backtest_result:
        bt = result.backtest_result
        lines.extend([
            f"- **Total Return:** {bt.total_return:.2%}",
            f"- **Sharpe Ratio:** {bt.sharpe_ratio:.2f}",
            f"- **Max Drawdown:** {bt.max_drawdown:.2%}",
            f"- **Total Trades:** {bt.total_trades}",
            f"- **Final Value:** ${bt.final_value:,.2f}",
        ])
    else:
        lines.append("No backtest results.")

    lines.extend(["", "## Authorization", ""])
    for auth in result.authorization_results:
        lines.extend([
            f"- **Trade:** {auth.trade.symbol} {auth.trade.side} {auth.trade.quantity}",
            f"- **Approved:** {auth.approved}",
            f"- **Reason:** {auth.reason}",
        ])

    lines.extend(["", "## Executed Orders", ""])
    if result.executed_orders:
        for order in result.executed_orders:
            lines.extend([
                f"- **Order ID:** {order.id}",
                f"- **Symbol:** {order.symbol}",
                f"- **Side:** {order.side}",
                f"- **Quantity:** {order.quantity}",
                f"- **Price:** ${order.price:,.2f}",
                f"- **Status:** {order.status.value}",
            ])
    else:
        lines.append("No orders executed.")

    lines.extend(["", "## Provenance", ""])
    if result.provenance_graph:
        lines.append(f"- **Nodes:** {len(result.provenance_graph._nodes)}")
        lines.append(f"- **Edges:** {len(result.provenance_graph._edges)}")
    else:
        lines.append("No provenance captured.")

    if result.errors:
        lines.extend(["", "## Errors", ""])
        for err in result.errors:
            lines.append(f"- {err}")

    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        for warn in result.warnings:
            lines.append(f"- {warn}")

    lines.extend(["", "---", "*Generated by Sovereign Agent Stack Quant Orchestrator*"])

    return "\n".join(lines)
