"""MCP server for ARGO integration.

Exposes SAS tools via MCP protocol for ARGO harness integration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def check_sovereignty(config_path: str = "sas.yaml") -> dict:
    """Check the current sovereignty score."""
    from sas.core.config import parse_sas_yaml
    from sas.core.scoring import generate_report

    config = parse_sas_yaml(Path(config_path))
    report = generate_report(config)
    return {
        "score": report.score,
        "verdict": report.verdict,
        "owned": report.owned_count,
        "total": report.total_count,
        "layers": [
            {"name": l.name, "status": l.scored_as.value, "reasoning": l.reasoning}
            for l in report.layers
        ],
    }


def query_knowledge(query: str, source: str = "~/sas-knowledge", store: str | None = None) -> list[dict]:
    """Query the compile-time knowledge graph.

    When no Layer 6 plugin is registered, behaves exactly as before —
    compiles fresh from the markdown directory ``source`` on every call
    and returns ``[{"label": ..., "content": ...}]``.

    When a plugin *is* registered (e.g. TIE), ``source`` is interpreted
    by that plugin (typically a path to a pre-compiled graph export, not
    a markdown directory). Pass ``store`` to query a persisted graph
    instead of recompiling on every call.
    """
    from pathlib import Path
    from sas.layers.knowledge_resolver import resolve_knowledge_backend, compile_source

    store_path = store if store else ":memory:"
    adapter, kind = resolve_knowledge_backend(store_path=store_path)

    if store:
        graph = adapter.load()
    else:
        graph = compile_source(adapter, Path(source).expanduser())

    results = adapter.query(graph, query)
    return [
        {"label": r.label, "content": r.properties.get("content", "")}
        for r in results
    ]


def pay_for_resource(
    resource: str,
    price: float,
    currency: str = "USD",
) -> dict:
    """Pay for a resource using the virtual card."""
    from sas.layers.payments import (
        PaymentRequirement,
        SpendingLimit,
        VirtualCardAdapter,
    )

    adapter = VirtualCardAdapter(limit=SpendingLimit(daily=1000, per_transaction=500, currency=currency))
    receipt = adapter.pay(PaymentRequirement(
        resource=resource,
        price=price,
        currency=currency,
        methods=["card"],
        cadence="one_shot",
        metadata={},
    ))
    return {
        "payment_id": receipt.payment_id,
        "status": receipt.status,
        "amount": receipt.amount,
        "currency": receipt.currency,
    }


# MCP tool registry
MCP_TOOLS = {
    "check_sovereignty": {
        "function": check_sovereignty,
        "description": "Check the current sovereignty score and get layer status",
        "parameters": {
            "type": "object",
            "properties": {
                "config_path": {
                    "type": "string",
                    "description": "Path to sas.yaml",
                    "default": "sas.yaml",
                }
            },
        },
    },
    "query_knowledge": {
        "function": query_knowledge,
        "description": "Query the compile-time knowledge graph",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query text",
                },
                "source": {
                    "type": "string",
                    "description": "Path to knowledge source directory",
                    "default": "~/sas-knowledge",
                },
            },
            "required": ["query"],
        },
    },
    "pay_for_resource": {
        "function": pay_for_resource,
        "description": "Pay for a resource using the virtual card",
        "parameters": {
            "type": "object",
            "properties": {
                "resource": {
                    "type": "string",
                    "description": "Resource identifier",
                },
                "price": {
                    "type": "number",
                    "description": "Price to pay",
                },
                "currency": {
                    "type": "string",
                    "description": "Currency (default: USD)",
                    "default": "USD",
                },
            },
            "required": ["resource", "price"],
        },
    },
}


def handle_mcp_request(request: dict) -> dict:
    """Handle an MCP request."""
    tool_name = request.get("tool", "")
    params = request.get("params", {})

    tool = MCP_TOOLS.get(tool_name)
    if not tool:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        result = tool["function"](**params)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


def main() -> None:
    """Run the MCP server."""
    import sys

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = handle_mcp_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON"}), flush=True)


if __name__ == "__main__":
    main()
