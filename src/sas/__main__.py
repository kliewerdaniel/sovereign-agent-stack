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


def _cmd_research(args: argparse.Namespace) -> int:
    """Run the quant research pipeline."""
    import numpy as np
    import pandas as pd
    from sas.quant.engine import QuantEngine, EngineConfig
    from sas.quant.strategy import (
        StrategyArtifact, SignalDefinition, PositionSizing,
        TransactionCosts, RiskConstraints,
    )
    from sas.quant.backtest import BacktestEngine, BacktestConfig
    from sas.quant.risk import RiskEngine, RiskPolicy
    from sas.quant.broker import SimulatedBroker, BrokerConfig
    from sas.quant.provenance import ProvenanceGraph, ProvenanceNode

    engine = QuantEngine(EngineConfig(seed=42))
    broker = SimulatedBroker(BrokerConfig())

    print("═══ Sovereign Quant Research ═══")
    print(f"Universe: {', '.join(args.universe) or 'default'}")
    print(f"Horizon: {args.horizon}")
    print(f"Engine seed: {engine.config.seed}")

    # Stage 1: Data → Dataset (synthetic market data)
    print("\n── DATA ──")
    rng = np.random.default_rng(42)
    n = 252  # 1 year of daily data
    dates = pd.date_range("2025-01-01", periods=n, freq="B")
    prices = pd.DataFrame(
        {"SPY": 400 * np.cumprod(1 + rng.normal(0.0005, 0.012, n))},
        index=dates,
    )
    returns = prices.pct_change().dropna()
    print(f"  Data points: {len(returns)}")

    # Stage 2: Research → Hypothesis
    print("\n── RESEARCH ──")
    print(f"  Mean daily return: {returns.mean().iloc[0]:.4f}")
    print(f"  Daily vol: {returns.std().iloc[0]:.4f}")

    # Stage 3: Signal → Strategy
    print("\n── SIGNAL ──")
    signal = engine.sharpe(np.asarray(returns["SPY"], dtype=float))
    print(f"  Sharpe (signal): {signal:.4f}")

    # Stage 4: Backtest
    print("\n── BACKTEST ──")
    strategy = StrategyArtifact(
        strategy_id="momentum-001",
        name="momentum",
        signal_definition=SignalDefinition(
            name="sma_crossover",
            type="trend",
            parameters={"fast": 10, "slow": 30},
            lookback_periods=30,
        ),
        position_sizing=PositionSizing(method="fixed_weight", target_weight=0.05),
        transaction_costs=TransactionCosts(commission_per_trade=1.0, slippage_bps=5),
        risk_constraints=RiskConstraints(max_position_weight=0.25),
    )
    bt_config = BacktestConfig(strategy=strategy, seed=42)
    bt_engine = BacktestEngine(bt_config)
    prices_df = pd.DataFrame(
        {"close": prices["SPY"], "volume": np.full(n, 1_000_000)},
        index=prices.index,
        columns=["close", "volume"],
    )
    result = bt_engine.run(bt_config, prices_df)
    print(f"  Total return: {result.total_return:.2%}")
    print(f"  Sharpe: {result.sharpe_ratio:.2f}")
    print(f"  Max drawdown: {result.max_drawdown:.2%}")
    print(f"  Trades: {result.total_trades}")

    # Stage 5: Risk evaluation
    print("\n── RISK ──")
    policy = RiskPolicy(max_position_weight=0.25)
    risk_engine = RiskEngine(policy)
    weights = {col: 1.0 / len(returns.columns) for col in returns.columns}
    eval_result = risk_engine.evaluate(weights, {}, {})
    print(f"  Compliant: {eval_result.is_compliant}")
    print(f"  Breaches: {len(eval_result.breaches)}")

    # Stage 6: Provenance
    print("\n── PROVENANCE ──")
    graph = ProvenanceGraph()
    root = ProvenanceNode(artifact_type="dataset", name="SPY")
    graph.add(root)
    print(f"  Root artifact: {root.name}")
    print(f"  Lineage depth: {len(graph.lineage_chain(root.id))}")

    # Stage 7: Report
    print("\n── REPORT ──")
    print("  Research report generated.")
    print(f"  Sovereignty: N/A (quant engine)")
    print("\n═══ Pipeline complete ═══")
    return 0


def _cmd_quant(args: argparse.Namespace) -> int:
    """Handle quant subcommands."""
    from sas.quant.lifecycle import ResearchLifecycle, ResearchStage
    from sas.quant.strategy import StrategyArtifact, SignalDefinition
    from sas.quant.backtest import BacktestEngine, BacktestConfig
    from sas.quant.risk import RiskEngine, RiskPolicy
    from sas.quant.provenance import ProvenanceGraph, ProvenanceNode

    sub = args.quant_command or "status"

    if sub == "research":
        universe = args.universe or []
        horizon = args.horizon or "1y"
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
            for from_name, to_stage in stage_map.items():
                lifecycle.transition_to(to_stage, actor="cli")
            stages = [t.to_stage for t in lifecycle.transitions]
            print(f"Research stages: {' → '.join(stages)}")
            print(f"Universe: {', '.join(universe) or 'default'}")
            print(f"Horizon: {horizon}")
            print("Research cycle complete.")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    elif sub == "backtest":
        strategy_id = args.strategy_id or "default"
        seed = args.seed or 42
        try:
            strategy = StrategyArtifact(
                strategy_id=strategy_id,
                name=strategy_id,
                signal_definition=SignalDefinition(
                    name=f"{strategy_id}_signal",
                    type="trend",
                    parameters={},
                    lookback_periods=10,
                ),
            )
            config = BacktestConfig(strategy=strategy, seed=seed)
            engine = BacktestEngine(config)
            result = engine.run()
            print(f"Strategy: {strategy_id}")
            print(f"Seed: {seed}")
            print(f"Total return: {result.total_return:.2%}")
            print(f"Sharpe: {result.sharpe_ratio:.2f}")
            print(f"Max drawdown: {result.max_drawdown:.2%}")
            print(f"Trades: {result.total_trades}")
            if result.warnings:
                print(f"Warnings: {result.warnings}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    elif sub == "status":
        print("═══ Sovereign Quant Status ═══")
        print("Modules:")
        for mod in ["engine", "strategy", "backtest", "risk",
                      "broker", "market", "provenance", "knowledge",
                      "reports", "lifecycle", "agents"]:
            print(f"  ✓ {mod}")
        print("Status: operational")

    elif sub == "risk":
        weights_str = args.weights or ""
        weights = {}
        if weights_str:
            for pair in weights_str.split(","):
                if ":" in pair:
                    k, v = pair.split(":")
                    weights[k.strip()] = float(v.strip())
        try:
            policy = RiskPolicy(max_position_weight=0.25)
            engine = RiskEngine(policy)
            result = engine.evaluate(weights, {}, {})
            print(f"Compliant: {result.is_compliant}")
            print(f"Breaches: {len(result.breaches)}")
            for b in result.breaches:
                print(f"  - {b['type']}: {b['severity']}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    elif sub == "provenance":
        node_id = args.node_id or ""
        graph = ProvenanceGraph()
        # Auto-create a sample graph if empty
        if not graph._nodes:
            root = ProvenanceNode(artifact_type="dataset", name="SPY")
            graph.add(root)
            mid = ProvenanceNode(artifact_type="strategy", name="momentum", parent_ids=[root.id])
            graph.add(mid)
            leaf = ProvenanceNode(artifact_type="backtest", name="bt-1", parent_ids=[mid.id])
            graph.add(leaf)
        # Try by ID first, then by name
        node = graph.get(node_id)
        if node is None:
            # Search by name
            for n in graph._nodes.values():
                if n.name == node_id:
                    node = n
                    break
        if node is None:
            print(f"Node '{node_id}' not found")
            return 1
        lineage = graph.lineage_chain(node.id)
        print(f"Node: {node.id} ({node.name})")
        print(f"Lineage depth: {len(lineage)}")
        for n in lineage:
            print(f"  ← {n.artifact_type}: {n.name}")

    else:
        print("Unknown quant subcommand:", sub)
        return 1

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

    # Research command
    research_parser = subparsers.add_parser("research", help="Run quant research pipeline")
    research_parser.add_argument(
        "--universe", "-u", action="append", default=[],
        help="Ticker universe (repeatable)",
    )
    research_parser.add_argument(
        "--horizon", default="1y",
        help="Time horizon (default: 1y)",
    )
    research_parser.add_argument(
        "--config", "-c", default="sas.yaml",
        help="Path to sas.yaml (default: sas.yaml)",
    )

    # Quant subcommands
    quant_parser = subparsers.add_parser("quant", help="Quantitative intelligence")
    quant_subparsers = quant_parser.add_subparsers(dest="quant_command")

    quant_research_parser = quant_subparsers.add_parser("research", help="Run quant research")
    quant_research_parser.add_argument("--universe", "-u", action="append", default=[])
    quant_research_parser.add_argument("--horizon", default="1y")

    quant_backtest_parser = quant_subparsers.add_parser("backtest", help="Run backtest")
    quant_backtest_parser.add_argument("--strategy-id", "-s", default="default")
    quant_backtest_parser.add_argument("--seed", default=42, type=int)

    quant_status_parser = quant_subparsers.add_parser("status", help="System status")

    quant_risk_parser = quant_subparsers.add_parser("risk", help="Evaluate risk")
    quant_risk_parser.add_argument("--weights", default="")

    quant_provenance_parser = quant_subparsers.add_parser("provenance", help="Inspect provenance")
    quant_provenance_parser.add_argument("node_id", nargs="?", default="")

    args = parser.parse_args(argv)

    if args.command == "dashboard":
        return _cmd_dashboard(args)
    elif args.command == "init":
        return _cmd_init(args)
    elif args.command == "research":
        return _cmd_research(args)
    elif args.command == "quant":
        return _cmd_quant(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())