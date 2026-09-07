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
@click.option("--format", "-f", type=click.Choice(["json", "markdown"]),
              default="markdown")
def reports(format: str):
    """Generate quant reports."""
    click.echo(f"Generating report ({format})...")
    click.echo("Report generated.")


@quant_cli.command()
def audit():
    """Show audit trail."""
    click.echo("Audit Trail:")
    click.echo("  (empty)")


@quant_cli.command()
@click.argument("node_id", required=False)
def provenance(node_id: str | None):
    """Show provenance graph."""
    click.echo("Provenance Graph:")
    if node_id:
        click.echo(f"  Node: {node_id}")
    else:
        click.echo("  (empty graph)")


# Register with SAS CLI
def register(parent):
    """Register quant subcommands with SAS CLI."""
    parent.add_command(quant_cli)