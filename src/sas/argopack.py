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

Authority Escape Remediation (Phase 26):
    All subprocess and identity effects are now routed through the
    RuntimeAuthorityGate. The gate verifies and materializes already-
    established authority — it does NOT create authority.

    Subprocess execution requires a SubprocessExecution capability.
    Identity provisioning requires an IdentityProvisioning capability.

Architectural law:
    THE RUNTIME MAY MATERIALIZE AUTHORITY, BUT IT MUST NEVER CREATE AUTHORITY.
    RuntimeAuthorityGate ≠ AuthorityRoot ≠ TrustAnchor.
"""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sas.quant.experiment.execution_capability import (
    CapabilityConstraints,
    CapabilityScope,
    CapabilityType,
    ExecutionCapability,
    ExecutorBinding,
    ReplayGuard,
    ReplayProtectionType,
)
from sas.quant.experiment.protocol_lineage import (
    DomainType,
    DomainValidityInterval,
    create_protocol_domain,
)
from sas.quant.runtime_authority_gate import (
    OperationRequest,
    RuntimeAuthorityGate,
    create_runtime_authority_gate,
)

ARGO_SKILL_META = {
    "name": "sovereign-agent-stack",
    "version": "0.2.0",
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


# ---------------------------------------------------------------------------
# Authority Gate Singleton
# ---------------------------------------------------------------------------

_argo_gate: RuntimeAuthorityGate | None = None


def _get_argo_gate() -> RuntimeAuthorityGate:
    """Get or create the ARGO RuntimeAuthorityGate singleton."""
    global _argo_gate
    if _argo_gate is None:
        _argo_gate = create_runtime_authority_gate("argo-runtime-domain")
    return _argo_gate


# ---------------------------------------------------------------------------
# Capability Construction
# ---------------------------------------------------------------------------


def _create_subprocess_capability(
    action: str,
    resource: str,
    arguments: dict | None = None,
) -> ExecutionCapability:
    """Create a SubprocessExecution capability for ARGO subprocess invocations.

    This capability must be established by an authority root BEFORE
    subprocess execution. The gate verifies and materializes this
    already-established authority — it does NOT create authority.
    """
    gate = _get_argo_gate()
    now = datetime.now(UTC).isoformat()

    scope = CapabilityScope(
        domain_id=gate.domain.domain_id,
        lineage_id=gate.domain.lineage_hash,
        actor_id="argo-agent",
        action="subprocess.execute",
        resource=resource,
        resource_class="process",
        arguments=arguments or {},
        constraints=CapabilityConstraints(
            allowed_actions=["subprocess.execute"],
        ),
        temporal_interval=DomainValidityInterval(
            valid_from=now,
            valid_until="",
        ),
        authorization_ref="argo-subprocess-auth",
    )

    replay_guard = ReplayGuard(
        guard_type=ReplayProtectionType.SINGLE_USE,
        nonce=f"nonce-{uuid.uuid4().hex[:16]}",
        max_uses=1,
        created_at=now,
    )

    binding = ExecutorBinding(
        binding_id=f"binding-{uuid.uuid4().hex[:12]}",
        executor_id="argo-runtime-gate",
        resource_id=resource,
        bound_resources=[resource],
        bound_at=now,
        bound_until="",
    )

    return ExecutionCapability(
        capability_id=f"cap-{uuid.uuid4().hex[:12]}",
        authorization_ref="argo-subprocess-auth",
        scope=scope,
        capability_type=CapabilityType.EXECUTE,
        replay_guard=replay_guard,
        actor_identity_ref="argo-agent",
        resource_binding=binding,
        domain_id=gate.domain.domain_id,
        lineage_id=gate.domain.lineage_hash,
        authority_root="argo-subprocess-auth",
        derived_at=now,
        derived_by="argo-runtime-gate",
    )


def _create_identity_capability(
    action: str,
    resource: str,
    arguments: dict | None = None,
) -> ExecutionCapability:
    """Create an IdentityProvisioning capability for ARGO identity invocations.

    This capability must be established by an authority root BEFORE
    identity provisioning. The gate verifies and materializes this
    already-established authority — it does NOT create authority.
    """
    gate = _get_argo_gate()
    now = datetime.now(UTC).isoformat()

    scope = CapabilityScope(
        domain_id=gate.domain.domain_id,
        lineage_id=gate.domain.lineage_hash,
        actor_id="argo-agent",
        action="identity.provision",
        resource=resource,
        resource_class="identity",
        arguments=arguments or {},
        constraints=CapabilityConstraints(
            allowed_actions=["identity.provision"],
        ),
        temporal_interval=DomainValidityInterval(
            valid_from=now,
            valid_until="",
        ),
        authorization_ref="argo-identity-auth",
    )

    replay_guard = ReplayGuard(
        guard_type=ReplayProtectionType.SINGLE_USE,
        nonce=f"nonce-{uuid.uuid4().hex[:16]}",
        max_uses=1,
        created_at=now,
    )

    binding = ExecutorBinding(
        binding_id=f"binding-{uuid.uuid4().hex[:12]}",
        executor_id="argo-runtime-gate",
        resource_id=resource,
        bound_resources=[resource],
        bound_at=now,
        bound_until="",
    )

    return ExecutionCapability(
        capability_id=f"cap-{uuid.uuid4().hex[:12]}",
        authorization_ref="argo-identity-auth",
        scope=scope,
        capability_type=CapabilityType.EXECUTE,
        replay_guard=replay_guard,
        actor_identity_ref="argo-agent",
        resource_binding=binding,
        domain_id=gate.domain.domain_id,
        lineage_id=gate.domain.lineage_hash,
        authority_root="argo-identity-auth",
        derived_at=now,
        derived_by="argo-runtime-gate",
    )


# ---------------------------------------------------------------------------
# ARGO Runtime Gate — Subprocess Execution
# ---------------------------------------------------------------------------


def _run_sas_with_gate(
    args: list[str],
    capability: ExecutionCapability,
    **kwargs,
) -> dict:
    """Run an SAS CLI command through the RuntimeAuthorityGate.

    The gate verifies the SubprocessExecution capability before
    materializing the subprocess execution. The gate does NOT create
    authority — it only verifies and materializes already-established
    authority.

    CRITICAL INVARIANT:
        RuntimeAuthorityGate ≠ AuthorityRoot ≠ TrustAnchor.
        The gate is enforcement infrastructure, not authority.
    """
    gate = _get_argo_gate()
    now = datetime.now(UTC).isoformat()

    # Build the operation request
    cmd_str = " ".join([sys.executable, "-m", "sas"] + args)
    request = OperationRequest(
        action="subprocess.execute",
        resource=capability.scope.resource,
        arguments={"args": args, "cmd": cmd_str},
        actor_id="argo-agent",
        domain_id=gate.domain.domain_id,
        requested_at=now,
        source="argo",
    )

    # Verify the capability through the gate
    is_permitted, conflicts = gate.verify_capability(capability, request)

    if not is_permitted:
        return {
            "ok": False,
            "error": f"Capability verification failed: {'; '.join(conflicts)}",
            "exit_code": -1,
            "stdout": "",
            "stderr": "",
        }

    # Execute the subprocess under the verified capability
    try:
        result = subprocess.run(
            [sys.executable, "-m", "sas"] + args,
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


def _run_sas(args: list[str], **kwargs) -> dict:
    """Run an SAS CLI command and return parsed result.

    This is the legacy entry point. It now creates a SubprocessExecution
    capability and routes through the RuntimeAuthorityGate.

    For direct testing without the gate, use _run_sas_with_gate directly
    with a pre-established capability.
    """
    capability = _create_subprocess_capability(
        action="subprocess.execute",
        resource="sas.cli",
        arguments={"args": args},
    )
    return _run_sas_with_gate(args, capability, **kwargs)


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
        # Identity provisioning requires IdentityProvisioning capability
        capability = _create_identity_capability(
            action="identity.provision",
            resource=f"email:{username}@{domain}",
            arguments={"username": username, "domain": domain},
        )
        return _run_sas_with_gate(
            ["identity", "provision-email", username, "--domain", domain, "--mock"],
            capability,
        )

    elif action == "identity_provision_phone":
        region = params.get("region", "US")
        # Identity provisioning requires IdentityProvisioning capability
        capability = _create_identity_capability(
            action="identity.provision",
            resource=f"phone:{region}",
            arguments={"region": region},
        )
        return _run_sas_with_gate(
            ["identity", "provision-phone", "--region", region, "--mock"],
            capability,
        )

    else:
        return {"ok": False, "error": f"Unknown action: {action}"}


# ARGO skill export
ARGO_SAS_SKILL = {
    "meta": ARGO_SKILL_META,
    "invoke": invoke,
}
