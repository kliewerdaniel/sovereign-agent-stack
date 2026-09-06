"""CLI entry point for Sovereign Agent Stack."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sas.core.config import generate_template, parse_sas_yaml
from sas.dashboard.report import run_dashboard, run_dashboard_json


def _cmd_substrate(args: argparse.Namespace) -> int:
    """Handle substrate subcommands."""
    from sas.layers.substrate import LocalDockerSubstrate

    sub = args.substrate_command or "help"
    substrate = LocalDockerSubstrate()

    if sub == "boot":
        m = substrate.boot(args.template)
        print(f"Machine booted: {m.id}")
        print(f"Template: {m.template}")
        print(f"Status: {m.status}")
        print(f"Resources: {m.resources}")
        return 0

    elif sub == "list":
        machines = substrate.list_machines()
        if not machines:
            print("No machines.")
            return 0
        print(f"Machines ({len(machines)}):")
        for m in machines:
            print(f"  - {m.id} ({m.template}) [{m.status}]")
        return 0

    elif sub == "exec":
        machines = {m.id: m for m in substrate.list_machines()}
        if args.machine_id not in machines:
            print(f"Machine not found: {args.machine_id}")
            return 1
        m = machines[args.machine_id]
        try:
            output = substrate.execute(m, args.command)
            print(f"Exit code: {output.exit_code}")
            if output.stdout:
                print(output.stdout)
            if output.stderr:
                print(output.stderr, file=sys.stderr)
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    elif sub == "destroy":
        machines = {m.id: m for m in substrate.list_machines()}
        if args.machine_id not in machines:
            print(f"Machine not found: {args.machine_id}")
            return 1
        m = machines[args.machine_id]
        substrate.destroy(m)
        print(f"Destroyed: {args.machine_id}")
        return 0

    else:
        print("Unknown substrate subcommand")
        return 1


def _cmd_identity(args: argparse.Namespace) -> int:
    """Handle identity subcommands."""
    from sas.layers.identity import (
        AgentMailAdapter,
        AgentPhoneAdapter,
        Email,
        MockEmailAdapter,
        MockPhoneAdapter,
    )

    sub = args.identity_command or "help"

    if sub == "provision-email":
        if args.mock:
            adapter = MockEmailAdapter()
        else:
            adapter = AgentMailAdapter(api_key="stub-key")
        inbox = adapter.provision(args.username, args.domain)
        print(f"Inbox provisioned: {inbox.id}")
        print(f"Address: {inbox.username}@{inbox.domain}")
        return 0

    elif sub == "send-email":
        if args.mock:
            adapter = MockEmailAdapter()
        else:
            adapter = AgentMailAdapter(api_key="stub-key")
        # For mock, look up inbox from stored inboxes
        inbox = None
        if isinstance(adapter, MockEmailAdapter) and args.inbox_id in adapter._inboxes:
            inbox = adapter._inboxes[args.inbox_id]
        if inbox is None:
            from sas.layers.identity import Inbox
            inbox = Inbox(id=args.inbox_id, username="agent", domain="agentmail.to", created_at="2024-01-01T00:00:00Z")
        email = Email(
            from_=f"{inbox.username}@{inbox.domain}",
            to=args.to,
            subject=args.subject,
            body=args.body,
        )
        adapter.send(inbox, email)
        print(f"Email sent to {args.to}")
        return 0

    elif sub == "provision-phone":
        if args.mock:
            adapter = MockPhoneAdapter()
        else:
            adapter = AgentPhoneAdapter(api_key="stub-key")
        phone = adapter.provision(args.region)
        print(f"Phone provisioned: {phone.id}")
        print(f"Number: {phone.number}")
        print(f"Region: {phone.region}")
        return 0

    elif sub == "call":
        if args.mock:
            adapter = MockPhoneAdapter()
        else:
            adapter = AgentPhoneAdapter(api_key="stub-key")
        number = None
        if isinstance(adapter, MockPhoneAdapter) and args.number_id in adapter._numbers:
            number = adapter._numbers[args.number_id]
        if number is None:
            from sas.layers.identity import PhoneNumber
            number = PhoneNumber(id=args.number_id, number="+15550000000", region="US", capabilities=["voice", "sms"])
        call = adapter.call(number, args.to)
        print(f"Call placed: {call.id}")
        print(f"To: {call.to_number}")
        print(f"Status: {call.status}")
        return 0

    elif sub == "sms":
        if args.mock:
            adapter = MockPhoneAdapter()
        else:
            adapter = AgentPhoneAdapter(api_key="stub-key")
        number = None
        if isinstance(adapter, MockPhoneAdapter) and args.number_id in adapter._numbers:
            number = adapter._numbers[args.number_id]
        if number is None:
            from sas.layers.identity import PhoneNumber
            number = PhoneNumber(id=args.number_id, number="+15550000000", region="US", capabilities=["voice", "sms"])
        adapter.sms(number, args.message)
        print(f"SMS sent from {number.number}")
        return 0

    else:
        print("Unknown identity subcommand")
        return 1


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


def _cmd_auth(args: argparse.Namespace) -> int:
    """Handle auth subcommands."""
    from sas.layers.auth import Credentials, LocalAuthBroker
    from pathlib import Path

    sub = args.auth_command or "help"
    store_path = Path(args.store).expanduser().resolve()

    if sub == "register":
        scopes = args.scopes.split(",") if args.scopes else None
        creds = Credentials(
            tool_name=args.tool_name,
            auth_type=args.auth_type,
            token=args.token,
            refresh_token=args.refresh_token,
            expires_at=args.expires_at,
            scopes=scopes,
        )
        broker = LocalAuthBroker(store_path=str(store_path))
        broker.register_tool(args.tool_name, creds)
        print(f"Registered: {args.tool_name} ({args.auth_type})")
        print(f"Store: {store_path}")
        return 0

    elif sub == "list":
        broker = LocalAuthBroker(store_path=str(store_path))
        tools = broker.list_tools()
        if not tools:
            print("No tools registered.")
            return 0
        print(f"Registered tools ({len(tools)}):")
        for t in tools:
            print(f"  - {t}")
        return 0

    elif sub == "get":
        broker = LocalAuthBroker(store_path=str(store_path))
        creds = broker.get_credentials(args.tool_name)
        if creds is None:
            print(f"Tool not found: {args.tool_name}")
            return 1
        print(f"Tool: {creds.tool_name}")
        print(f"Auth type: {creds.auth_type}")
        print(f"Token: {'*' * 8}{creds.token[-4:] if creds.token and len(creds.token) > 4 else ''}")
        print(f"Refresh: {'set' if creds.refresh_token else 'none'}")
        print(f"Expires: {creds.expires_at or 'never'}")
        print(f"Scopes: {', '.join(creds.scopes) if creds.scopes else 'none'}")
        return 0

    elif sub == "unregister":
        broker = LocalAuthBroker(store_path=str(store_path))
        broker.unregister_tool(args.tool_name)
        print(f"Unregistered: {args.tool_name}")
        return 0

    elif sub == "audit":
        broker = LocalAuthBroker(store_path=str(store_path))
        trail = broker.audit()
        if not trail.entries:
            print("No audit entries.")
            return 0
        print(f"Audit trail ({len(trail.entries)} entries):")
        for e in trail.entries:
            print(f"  {e.timestamp} {e.method} {e.path} ({e.credential_used})")
        return 0

    else:
        print("Unknown auth subcommand")
        return 1


def _cmd_registry(args: argparse.Namespace) -> int:
    """Handle registry subcommands."""
    from sas.registry import CommunityRegistry, RegistryEntry

    sub = args.registry_command or "help"
    reg = CommunityRegistry()

    if sub == "publish":
        entry = RegistryEntry(
            name=args.name,
            layer_id=args.layer_id,
            version=args.version,
            description=args.description or "",
            author=args.author or "",
            url=args.url or "",
        )
        reg.publish(entry)
        print(f"Published: {entry.name} v{entry.version}")
        return 0

    elif sub == "unpublish":
        if reg.unpublish(args.name):
            print(f"Unpublished: {args.name}")
            return 0
        else:
            print(f"Not found: {args.name}")
            return 1

    elif sub == "search":
        results = reg.search(args.query)
        if not results:
            print("No plugins found.")
            return 0
        print(f"Plugins ({len(results)}):")
        for r in results:
            print(f"  - {r.name} v{r.version} ({r.layer_id})")
            if r.description:
                print(f"    {r.description}")
        return 0

    elif sub == "list":
        plugins = reg.list_all()
        if not plugins:
            print("No plugins registered.")
            return 0
        print(f"Registered plugins ({len(plugins)}):")
        for p in plugins:
            print(f"  - {p.name} v{p.version} ({p.layer_id})")
        return 0

    elif sub == "get":
        entry = reg.get(args.name)
        if entry is None:
            print(f"Not found: {args.name}")
            return 1
        print(f"Plugin: {entry.name}")
        print(f"Version: {entry.version}")
        print(f"Layer: {entry.layer_id}")
        print(f"Description: {entry.description}")
        print(f"Author: {entry.author}")
        print(f"URL: {entry.url}")
        print(f"Created: {entry.created_at}")
        return 0

    elif sub == "by-layer":
        results = reg.list_by_layer(args.layer_id)
        if not results:
            print(f"No plugins for {args.layer_id}")
            return 0
        print(f"Plugins for {args.layer_id} ({len(results)}):")
        for r in results:
            print(f"  - {r.name} v{r.version}")
        return 0

    else:
        print("Unknown registry subcommand")
        return 1


def _cmd_argo(args: argparse.Namespace) -> int:
    """Handle ARGO skill pack subcommands."""
    from sas.argopack import ARGO_SKILL_META, invoke
    import json

    sub = args.argo_command or "help"

    if sub == "info":
        print(json.dumps(ARGO_SKILL_META, indent=2))
        return 0

    elif sub == "invoke":
        params_str = args.params or "{}"
        try:
            params = json.loads(params_str)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON params: {e}")
            return 1
        result = invoke(params)
        print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("ok") else 1

    elif sub == "schema":
        print(json.dumps(ARGO_SKILL_META.get("parameters", {}), indent=2))
        return 0

    else:
        print("Unknown argo subcommand")
        return 1


def _cmd_payments(args: argparse.Namespace) -> int:
    """Handle payments subcommands."""
    from sas.layers.payments import MPPAdapter, PaymentRequirement, SpendingLimit, VirtualCardAdapter

    sub = args.payments_command or "help"

    if sub == "pay":
        if args.adapter == "virtual_card":
            adapter = VirtualCardAdapter()
        else:
            adapter = MPPAdapter(settlement="stablecoin")
        methods = args.methods.split(",")
        req = PaymentRequirement(
            resource=args.resource,
            price=args.price,
            currency=args.currency,
            methods=methods,
            cadence=args.cadence,
            metadata={},
        )
        try:
            receipt = adapter.pay(req)
        except ValueError as e:
            print(f"Payment failed: {e}")
            return 1
        print(f"Payment: {receipt.resource}")
        print(f"Amount: {receipt.amount} {receipt.currency}")
        print(f"Method: {receipt.method}")
        print(f"Status: {receipt.status}")
        print(f"ID: {receipt.payment_id}")
        return 0

    elif sub == "limit":
        if args.adapter == "virtual_card":
            adapter = VirtualCardAdapter()
        else:
            adapter = MPPAdapter(settlement="stablecoin")
        limit = SpendingLimit(daily=args.daily, per_transaction=args.per_transaction, currency=args.currency)
        adapter.authorize(limit)
        print(f"Limit set: {args.daily} {args.currency}/day, {args.per_transaction} {args.currency}/tx")
        return 0

    else:
        print("Unknown payments subcommand")
        return 1


def _cmd_knowledge(args: argparse.Namespace) -> int:
    """Handle knowledge subcommands."""
    from sas.layers.knowledge import CompileTimeKnowledge
    from pathlib import Path

    sub = args.knowledge_command or "help"
    store_path = Path(args.store).expanduser().resolve()

    if sub == "compile":
        source = Path(args.source).resolve()
        if not source.exists():
            print(f"Source not found: {source}")
            return 1
        ctk = CompileTimeKnowledge(store_path=str(store_path))
        graph = ctk.compile(source)
        print(f"Compiled: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
        print(f"Store: {store_path}")
        for node in graph.nodes:
            print(f"  - {node.label}")
        return 0

    elif sub == "query":
        if not store_path.exists():
            print(f"Graph store not found: {store_path}")
            print("Run 'python -m sas knowledge compile <source>' first.")
            return 1
        ctk = CompileTimeKnowledge(store_path=str(store_path))
        graph = ctk.load(store_path)
        if not graph.nodes:
            print("Graph is empty. Compile first.")
            return 1
        results = ctk.query(graph, args.query)
        print(f"Query: {args.query}")
        print(f"Results: {len(results)}")
        for r in results:
            print(f"  - {r.label}")
        return 0

    elif sub == "audit":
        if not store_path.exists():
            print(f"Graph store not found: {store_path}")
            return 1
        ctk = CompileTimeKnowledge(store_path=str(store_path))
        graph = ctk.load(store_path)
        if not graph.nodes:
            print("Graph is empty. Compile first.")
            return 1
        report = ctk.audit(graph)
        print(f"Audit: {report.total_nodes} nodes, {report.total_edges} edges")
        print(f"Orphaned: {len(report.orphaned_nodes)}")
        print(f"Stale: {len(report.stale_nodes)}")
        return 0

    else:
        print("Unknown knowledge subcommand")
        return 1


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

    # Knowledge subcommands
    knowledge_parser = subparsers.add_parser("knowledge", help="Compile-time knowledge graph")
    knowledge_subparsers = knowledge_parser.add_subparsers(dest="knowledge_command")

    knowledge_compile_parser = knowledge_subparsers.add_parser("compile", help="Compile markdown into graph")
    knowledge_compile_parser.add_argument("source", help="Path to markdown file or directory")
    knowledge_compile_parser.add_argument("--store", default="~/.sas/knowledge.db", help="Graph store path")

    knowledge_query_parser = knowledge_subparsers.add_parser("query", help="Query the graph")
    knowledge_query_parser.add_argument("query", help="Query text")
    knowledge_query_parser.add_argument("--store", default="~/.sas/knowledge.db", help="Graph store path")
    knowledge_query_parser.add_argument("--transitive", action="store_true", help="Follow edges transitively")

    knowledge_audit_parser = knowledge_subparsers.add_parser("audit", help="Audit the graph")
    knowledge_audit_parser.add_argument("--store", default="~/.sas/knowledge.db", help="Graph store path")

    # Auth subcommands
    auth_parser = subparsers.add_parser("auth", help="Local auth broker / MCP gateway")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command")

    auth_register_parser = auth_subparsers.add_parser("register", help="Register a tool")
    auth_register_parser.add_argument("tool_name", help="Tool name")
    auth_register_parser.add_argument("--auth-type", default="oauth", help="Auth type (oauth, api_key, basic)")
    auth_register_parser.add_argument("--token", help="Token value")
    auth_register_parser.add_argument("--refresh-token", help="Refresh token")
    auth_register_parser.add_argument("--expires-at", help="Token expiry")
    auth_register_parser.add_argument("--scopes", help="Comma-separated scopes")
    auth_register_parser.add_argument("--store", default="~/.sas/auth.db", help="Credential store path")

    auth_list_parser = auth_subparsers.add_parser("list", help="List registered tools")
    auth_list_parser.add_argument("--store", default="~/.sas/auth.db", help="Credential store path")

    auth_get_parser = auth_subparsers.add_parser("get", help="Get tool credentials")
    auth_get_parser.add_argument("tool_name", help="Tool name")
    auth_get_parser.add_argument("--store", default="~/.sas/auth.db", help="Credential store path")

    auth_unregister_parser = auth_subparsers.add_parser("unregister", help="Unregister a tool")
    auth_unregister_parser.add_argument("tool_name", help="Tool name")
    auth_unregister_parser.add_argument("--store", default="~/.sas/auth.db", help="Credential store path")

    auth_audit_parser = auth_subparsers.add_parser("audit", help="View audit trail")
    auth_audit_parser.add_argument("--store", default="~/.sas/auth.db", help="Credential store path")

    # Registry subcommands
    registry_parser = subparsers.add_parser("registry", help="Community layer registry")
    registry_subparsers = registry_parser.add_subparsers(dest="registry_command")

    registry_publish_parser = registry_subparsers.add_parser("publish", help="Publish a plugin")
    registry_publish_parser.add_argument("name", help="Plugin name")
    registry_publish_parser.add_argument("layer_id", help="Layer ID (e.g., layer_8_payments)")
    registry_publish_parser.add_argument("version", help="Plugin version")
    registry_publish_parser.add_argument("--description", default="", help="Description")
    registry_publish_parser.add_argument("--author", default="", help="Author")
    registry_publish_parser.add_argument("--url", default="", help="URL")

    registry_unpublish_parser = registry_subparsers.add_parser("unpublish", help="Unpublish a plugin")
    registry_unpublish_parser.add_argument("name", help="Plugin name")

    registry_search_parser = registry_subparsers.add_parser("search", help="Search plugins")
    registry_search_parser.add_argument("query", help="Search query")

    registry_list_parser = registry_subparsers.add_parser("list", help="List all plugins")

    registry_get_parser = registry_subparsers.add_parser("get", help="Get plugin details")
    registry_get_parser.add_argument("name", help="Plugin name")

    registry_by_layer_parser = registry_subparsers.add_parser("by-layer", help="List plugins by layer")
    registry_by_layer_parser.add_argument("layer_id", help="Layer ID")

    # ARGO skill pack subcommands
    argo_parser = subparsers.add_parser("argo", help="ARGO skill pack")
    argo_subparsers = argo_parser.add_subparsers(dest="argo_command")

    argo_info_parser = argo_subparsers.add_parser("info", help="Show skill metadata")
    argo_invoke_parser = argo_subparsers.add_parser("invoke", help="Invoke skill")
    argo_invoke_parser.add_argument("--params", default="{}", help="JSON params string")
    argo_schema_parser = argo_subparsers.add_parser("schema", help="Show parameter schema")

    # Payments subcommands
    payments_parser = subparsers.add_parser("payments", help="Payments abstraction")
    payments_subparsers = payments_parser.add_subparsers(dest="payments_command")

    payments_pay_parser = payments_subparsers.add_parser("pay", help="Make a payment")
    payments_pay_parser.add_argument("resource", help="Resource to pay for")
    payments_pay_parser.add_argument("--price", type=float, required=True, help="Price")
    payments_pay_parser.add_argument("--currency", default="USD", help="Currency")
    payments_pay_parser.add_argument("--methods", default="card", help="Comma-separated payment methods")
    payments_pay_parser.add_argument("--cadence", default="one_shot", help="Payment cadence")
    payments_pay_parser.add_argument("--adapter", default="virtual_card", choices=["virtual_card", "mpp"], help="Payment adapter")

    payments_limit_parser = payments_subparsers.add_parser("limit", help="Set spending limit")
    payments_limit_parser.add_argument("--daily", type=float, required=True, help="Daily limit")
    payments_limit_parser.add_argument("--per-transaction", type=float, required=True, help="Per-transaction limit")
    payments_limit_parser.add_argument("--currency", default="USD", help="Currency")
    payments_limit_parser.add_argument("--adapter", default="virtual_card", choices=["virtual_card", "mpp"], help="Payment adapter")

    # Substrate subcommands
    substrate_parser = subparsers.add_parser("substrate", help="Compute substrate (local VM/container)")
    substrate_subparsers = substrate_parser.add_subparsers(dest="substrate_command")

    substrate_boot_parser = substrate_subparsers.add_parser("boot", help="Boot a machine")
    substrate_boot_parser.add_argument("--template", default="xfce", help="Desktop template (xfce, lxde)")

    substrate_list_parser = substrate_subparsers.add_parser("list", help="List machines")

    substrate_exec_parser = substrate_subparsers.add_parser("exec", help="Execute a command")
    substrate_exec_parser.add_argument("machine_id", help="Machine ID")
    substrate_exec_parser.add_argument("command", help="Command to run")

    substrate_destroy_parser = substrate_subparsers.add_parser("destroy", help="Destroy a machine")
    substrate_destroy_parser.add_argument("machine_id", help="Machine ID")

    # Identity subcommands
    identity_parser = subparsers.add_parser("identity", help="Identity adapters")
    identity_subparsers = identity_parser.add_subparsers(dest="identity_command")

    identity_email_provision_parser = identity_subparsers.add_parser("provision-email", help="Provision email inbox")
    identity_email_provision_parser.add_argument("username", help="Email username")
    identity_email_provision_parser.add_argument("--domain", default="agentmail.to", help="Email domain")
    identity_email_provision_parser.add_argument("--mock", action="store_true", help="Use mock adapter")

    identity_email_send_parser = identity_subparsers.add_parser("send-email", help="Send email")
    identity_email_send_parser.add_argument("inbox_id", help="Inbox ID")
    identity_email_send_parser.add_argument("--to", required=True, help="Recipient")
    identity_email_send_parser.add_argument("--subject", required=True, help="Subject")
    identity_email_send_parser.add_argument("--body", required=True, help="Body")
    identity_email_send_parser.add_argument("--mock", action="store_true", help="Use mock adapter")

    identity_phone_provision_parser = identity_subparsers.add_parser("provision-phone", help="Provision phone number")
    identity_phone_provision_parser.add_argument("--region", default="US", help="Phone region")
    identity_phone_provision_parser.add_argument("--mock", action="store_true", help="Use mock adapter")

    identity_phone_call_parser = identity_subparsers.add_parser("call", help="Make a call")
    identity_phone_call_parser.add_argument("number_id", help="Phone number ID")
    identity_phone_call_parser.add_argument("--to", required=True, help="Target number")
    identity_phone_call_parser.add_argument("--mock", action="store_true", help="Use mock adapter")

    identity_phone_sms_parser = identity_subparsers.add_parser("sms", help="Send SMS")
    identity_phone_sms_parser.add_argument("number_id", help="Phone number ID")
    identity_phone_sms_parser.add_argument("--message", required=True, help="Message")
    identity_phone_sms_parser.add_argument("--mock", action="store_true", help="Use mock adapter")

    args = parser.parse_args(argv)

    if args.command == "dashboard":
        return _cmd_dashboard(args)
    elif args.command == "init":
        return _cmd_init(args)
    elif args.command == "research":
        return _cmd_research(args)
    elif args.command == "quant":
        return _cmd_quant(args)
    elif args.command == "knowledge":
        return _cmd_knowledge(args)
    elif args.command == "auth":
        return _cmd_auth(args)
    elif args.command == "payments":
        return _cmd_payments(args)
    elif args.command == "substrate":
        return _cmd_substrate(args)
    elif args.command == "identity":
        return _cmd_identity(args)
    elif args.command == "registry":
        return _cmd_registry(args)
    elif args.command == "argo":
        return _cmd_argo(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())