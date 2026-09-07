"""ARGO skill pack for Sovereign Agent Stack integration.

This module provides an ARGO-compatible skill wrapper around SAS,
enabling ARGO agents to check sovereignty, compile knowledge,
and manage credentials via SAS CLI.

ARGO skill interface:
    - name: str
    - description: str
    - parameters: JSON Schema
    - invoke(input) -> output

Usage:
    from sas.argopack import ARGO_SAS_SKILL

    # In ARGO agent:
    result = ARGO_SAS_SKILL.invoke({"action": "sovereignty_check"})
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ARGO_SKILL_META = {
    "name": "sovereign-agent-stack",
    "version": "0.1.0",
    "description": "Check agent sovereignty, compile knowledge graphs, manage credentials",
    "author": "Sovereign Agent Stack contributors",
    "license": "MIT",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "sovereignty_check",
                    "compile_knowledge",
                    "query_knowledge",
                    "register_credential",
                    "list_credentials",
                    "audit_credentials",
                    "quant_status",
                    "substrate_list",
                    "substrate_boot",
                    "substrate_destroy",
                    "payments_pay",
                    "payments_limit",
                    "identity_provision_email",
                    "identity_provision_phone",
                ],
                "description": "SAS action to perform",
            },
            "config": {
                "type": "string",
                "description": "Path to sas.yaml (default: sas.yaml)",
            },
            "cache": {
                "type": "string",
                "description": "Path to cache directory (default: ~/.sas)",
            },
            "source": {
                "type": "string",
                "description": "Knowledge source path (for compile_knowledge)",
            },
            "query": {
                "type": "string",
                "description": "Query string (for query_knowledge)",
            },
            "tool_name": {
                "type": "string",
                "description": "Tool name (for register_credential)",
            },
            "token": {
                "type": "string",
                "description": "Token value (for register_credential)",
            },
            "resource": {
                "type": "string",
                "description": "Resource name (for payments_pay)",
            },
            "price": {
                "type": "number",
                "description": "Price (for payments_pay)",
            },
            "machine_id": {
                "type": "string",
                "description": "Machine ID (for substrate_destroy)",
            },
            "template": {
                "type": "string",
                "description": "Desktop template (for substrate_boot)",
            },
            "username": {
                "type": "string",
                "description": "Email username (for identity_provision_email)",
            },
            "domain": {
                "type": "string",
                "description": "Email domain (for identity_provision_email)",
            },
            "region": {
                "type": "string",
                "description": "Phone region (for identity_provision_phone)",
            },
        },
        "required": ["action"],
    },
}


def _run_sas(args: list[str], **kwargs) -> dict:
    """Run an SAS CLI command and return parsed result."""
    cmd = [sys.executable, "-m", "sas"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            **kwargs,
        )
        return {
            "ok": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Command timed out"}
    except FileNotFoundError:
        return {"ok": False, "error": "sas module not found. Install with: pip install sovereign-agent-stack"}


def invoke(params: dict[str, Any]) -> dict[str, Any]:
    """ARGO skill entry point.

    Args:
        params: Dict with 'action' and action-specific parameters.

    Returns:
        Dict with 'ok' (bool) and result data.
    """
    action = params.get("action", "")
    config = params.get("config", "sas.yaml")
    cache = params.get("cache", "~/.sas")

    if action == "sovereignty_check":
        result = _run_sas(["dashboard", "--config", config, "--cache", cache, "--json"])
        if result["ok"]:
            try:
                result["data"] = json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return result

    elif action == "compile_knowledge":
        source = params.get("source", "")
        if not source:
            return {"ok": False, "error": "Missing 'source' parameter"}
        store = params.get("store", str(Path(cache).expanduser() / "knowledge.db"))
        return _run_sas(["knowledge", "compile", source, "--store", store])

    elif action == "query_knowledge":
        query = params.get("query", "")
        if not query:
            return {"ok": False, "error": "Missing 'query' parameter"}
        store = params.get("store", str(Path(cache).expanduser() / "knowledge.db"))
        return _run_sas(["knowledge", "query", query, "--store", store])

    elif action == "register_credential":
        tool_name = params.get("tool_name", "")
        token = params.get("token", "")
        if not tool_name or not token:
            return {"ok": False, "error": "Missing 'tool_name' or 'token'"}
        auth_type = params.get("auth_type", "oauth")
        store = params.get("store", str(Path(cache).expanduser() / "auth.db"))
        return _run_sas([
            "auth", "register", tool_name,
            "--auth-type", auth_type,
            "--token", token,
            "--store", store,
        ])

    elif action == "list_credentials":
        store = params.get("store", str(Path(cache).expanduser() / "auth.db"))
        return _run_sas(["auth", "list", "--store", store])

    elif action == "audit_credentials":
        store = params.get("store", str(Path(cache).expanduser() / "auth.db"))
        return _run_sas(["auth", "audit", "--store", store])

    elif action == "quant_status":
        return _run_sas(["quant", "status"])

    elif action == "substrate_list":
        return _run_sas(["substrate", "list"])

    elif action == "substrate_boot":
        template = params.get("template", "xfce")
        return _run_sas(["substrate", "boot", "--template", template])

    elif action == "substrate_destroy":
        machine_id = params.get("machine_id", "")
        if not machine_id:
            return {"ok": False, "error": "Missing 'machine_id'"}
        return _run_sas(["substrate", "destroy", machine_id])

    elif action == "payments_pay":
        resource = params.get("resource", "")
        price = params.get("price")
        if not resource or price is None:
            return {"ok": False, "error": "Missing 'resource' or 'price'"}
        currency = params.get("currency", "USD")
        methods = params.get("methods", "card")
        cadence = params.get("cadence", "one_shot")
        adapter = params.get("adapter", "virtual_card")
        return _run_sas([
            "payments", "pay", resource,
            "--price", str(price),
            "--currency", currency,
            "--methods", methods,
            "--cadence", cadence,
            "--adapter", adapter,
        ])

    elif action == "payments_limit":
        daily = params.get("daily")
        per_tx = params.get("per_transaction")
        if daily is None or per_tx is None:
            return {"ok": False, "error": "Missing 'daily' or 'per_transaction'"}
        currency = params.get("currency", "USD")
        adapter = params.get("adapter", "virtual_card")
        return _run_sas([
            "payments", "limit",
            "--daily", str(daily),
            "--per-transaction", str(per_tx),
            "--currency", currency,
            "--adapter", adapter,
        ])

    elif action == "identity_provision_email":
        username = params.get("username", "")
        if not username:
            return {"ok": False, "error": "Missing 'username'"}
        domain = params.get("domain", "agentmail.to")
        return _run_sas(["identity", "provision-email", username, "--domain", domain, "--mock"])

    elif action == "identity_provision_phone":
        region = params.get("region", "US")
        return _run_sas(["identity", "provision-phone", "--region", region, "--mock"])

    else:
        return {"ok": False, "error": f"Unknown action: {action}"}


# ARGO skill export
ARGO_SAS_SKILL = {
    "meta": ARGO_SKILL_META,
    "invoke": invoke,
}
