"""CLI for Sovereign Agent Operations.

Provides command-line interface for managing agents, tools, and sovereignty.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from sas.core.config import parse_sas_yaml, generate_template
from sas.core.scoring import generate_report
from sas.runtime.orchestrator import AgentRuntime, FleetCoordinator
from sas.runtime.mcp_server import MCPServer
from sas.quant.cli import register as register_quant


@click.group()
@click.version_option(version="0.3.0", prog_name="sas")
def cli():
    """Sovereign Agent Stack CLI."""
    pass


@cli.command("init")
@click.option("--output", "-o", default="sas.yaml", help="Output config file path")
def init(output: str):
    """Initialize a new sas.yaml configuration file."""
    path = Path(output)
    generate_template(path)
    click.echo(f"Created template config: {path}")


@cli.command("dashboard")
@click.option("--config", "-c", default="sas.yaml", help="Path to sas.yaml")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def dashboard(config: str, as_json: bool, verbose: bool):
    """Run sovereignty dashboard."""
    config_path = Path(config)
    if not config_path.exists():
        click.echo(f"Config not found: {config_path}")
        click.echo("Run 'sas init' to create a template config.")
        sys.exit(1)
    
    sas_config = parse_sas_yaml(config_path)
    report = generate_report(sas_config)
    
    if as_json:
        output = {
            "score": report.score,
            "verdict": report.verdict,
            "owned": report.owned_count,
            "total": report.total_count,
            "layers": [
                {
                    "name": layer.name,
                    "status": layer.scored_as.value,
                    "reasoning": layer.reasoning,
                }
                for layer in report.layers
            ],
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo("═" * 50)
        click.echo("  SOVEREIGN AGENT STACK — DASHBOARD")
        click.echo("═" * 50)
        click.echo(f"  Score: {report.score:.2%}")
        click.echo(f"  Verdict: {report.verdict}")
        click.echo(f"  Owned: {report.owned_count}/{report.total_count}")
        click.echo("─" * 50)
        for layer in report.layers:
            status_icon = "✓" if layer.scored_as.value == "owned" else "✗"
            click.echo(f"  {status_icon} {layer.name}: {layer.scored_as.value}")
            if verbose:
                click.echo(f"    {layer.reasoning}")
        click.echo("═" * 50)


@cli.command("run")
@click.option("--config", "-c", default="sas.yaml", help="Path to sas.yaml")
@click.option("--query", "-q", help="Query to execute")
def run(config: str, query: str | None):
    """Run an agent session."""
    config_path = Path(config)
    if not config_path.exists():
        click.echo(f"Config not found: {config_path}")
        sys.exit(1)
    
    runtime = AgentRuntime.from_config(config_path)
    runtime.initialize()
    
    click.echo(f"Agent runtime initialized: {runtime.context.session_id}")
    click.echo(f"Sovereignty score: {runtime.context.sovereignty_asserter.score:.2f}")
    click.echo(f"Verdict: {runtime.context.sovereignty_asserter.verdict}")
    
    if query:
        click.echo(f"\nExecuting query: {query}")
        # In a real implementation, this would execute the query
        result = {"status": "ok", "query": query}
        click.echo(f"Result: {json.dumps(result, indent=2)}")
    
    runtime.shutdown()
    click.echo("\nRuntime shutdown complete.")


@cli.command("serve")
@click.option("--config", "-c", default="sas.yaml", help="Path to sas.yaml")
def serve(config: str):
    """Start MCP server."""
    config_path = Path(config)
    if not config_path.exists():
        click.echo(f"Config not found: {config_path}")
        sys.exit(1)
    
    click.echo("Starting MCP server...")
    server = MCPServer.from_config(config_path)
    server.serve()


@cli.command("fleet")
@click.option("--config", "-c", default="sas.yaml", help="Path to sas.yaml")
@click.option("--agents", "-n", default=1, help="Number of agents to spawn")
def fleet(config: str, agents: int):
    """Manage a fleet of agents."""
    config_path = Path(config)
    
    coordinator = FleetCoordinator()
    
    for i in range(agents):
        if config_path.exists():
            session_id = coordinator.spawn_agent(str(config_path))
        else:
            session_id = coordinator.spawn_agent()
        click.echo(f"Spawned agent {i+1}/{agents}: {session_id[:8]}...")
    
    status = coordinator.fleet_status()
    click.echo(f"\nFleet status: {status['agents']} agents")
    click.echo(f"Average sovereignty: {status['average_sovereignty_score']:.2f}")
    
    coordinator.shutdown_all()
    click.echo("Fleet shutdown complete.")


@cli.command("tools")
@click.option("--config", "-c", default="sas.yaml", help="Path to sas.yaml")
def tools(config: str):
    """List available tools."""
    config_path = Path(config)
    if config_path.exists():
        server = MCPServer.from_config(config_path)
    else:
        server = MCPServer.from_defaults()
    
    tool_list = server.list_tools()
    click.echo("Available tools:")
    for tool in tool_list:
        click.echo(f"  • {tool['name']}: {tool['description']}")


@cli.command("verify")
@click.option("--config", "-c", default="sas.yaml", help="Path to sas.yaml")
@click.option("--threshold", "-t", default=0.625, help="Minimum sovereignty threshold")
def verify(config: str, threshold: float):
    """Verify sovereignty meets threshold."""
    config_path = Path(config)
    if not config_path.exists():
        click.echo(f"Config not found: {config_path}")
        sys.exit(1)
    
    sas_config = parse_sas_yaml(config_path)
    report = generate_report(sas_config)
    
    if report.score >= threshold:
        click.echo(f"✓ Sovereignty verified: {report.score:.2%} >= {threshold:.2%}")
    else:
        click.echo(f"✗ Sovereignty below threshold: {report.score:.2%} < {threshold:.2%}")
        sys.exit(1)


# Register quant subcommands
register_quant(cli)

if __name__ == "__main__":
    cli()
