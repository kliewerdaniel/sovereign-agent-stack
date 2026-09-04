"""CLI entry point for Sovereign Agent Stack."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sas.core.config import generate_template, parse_sas_yaml
from sas.dashboard.report import run_dashboard, run_dashboard_json


def _cmd_dashboard(args: argparse.Namespace) -> int:
    """Run the sovereignty dashboard."""
    config_path = Path(args.config).resolve()
    cache_dir = Path(args.cache).resolve()

    if not config_path.exists():
        print(f"Config not found: {config_path}")
        print("Run 'python -m sas init' to create a template.")
        return 1

    if args.json:
        import json
        result = run_dashboard_json(config_path, cache_dir)
        print(json.dumps(result, indent=2))
    else:
        report_md = run_dashboard(config_path, cache_dir, verbose=args.verbose)
        print(report_md)

    return 0


def _cmd_init(args: argparse.Namespace) -> int:
    """Initialize a template sas.yaml."""
    config_path = Path(args.output).resolve()

    if config_path.exists():
        print(f"Config already exists: {config_path}")
        return 1

    generate_template(config_path)
    print(f"Template created: {config_path}")
    print("Edit the file to match your deployment, then run 'python -m sas dashboard'")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sas",
        description="Sovereign Agent Stack — local-first, compile-time AI agent framework",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0-alpha")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Dashboard command
    dash_parser = subparsers.add_parser("dashboard", help="Run the sovereignty dashboard")
    dash_parser.add_argument(
        "--config",
        default="sas.yaml",
        help="Path to sas.yaml (default: sas.yaml)",
    )
    dash_parser.add_argument(
        "--cache",
        default="~/.sas",
        help="Path to cache directory (default: ~/.sas)",
    )
    dash_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed reasoning for each layer",
    )
    dash_parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of markdown",
    )

    # Init command
    init_parser = subparsers.add_parser("init", help="Create a template sas.yaml")
    init_parser.add_argument(
        "--output",
        default="sas.yaml",
        help="Output path (default: sas.yaml)",
    )

    args = parser.parse_args(argv)

    if args.command == "dashboard":
        return _cmd_dashboard(args)
    elif args.command == "init":
        return _cmd_init(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
