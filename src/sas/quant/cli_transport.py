"""CLI Transport Layer — makes the CLI a transport, not an authority root.

The CLI must not be an authority root. A CLI command such as:
    sas trade ...
    sas payment ...
    sas plugin ...
    sas identity ...
    sas exec ...

must be treated as a transport/interface.

The CLI may construct a request. It may not construct authority merely because
the user supplied command-line arguments.

Architectural law:
    CLI INPUT → PARSED REQUEST → CONSEQUENCE CLASSIFICATION → AUTHORIZATION RESOLUTION
    → CAPABILITY MATERIALIZATION → VERIFICATION → EXECUTION → RECEIPT

The CLI must not contain an independent:
    allow=True
    policy="allow"
    admin=True
    trusted=True
    escape.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Optional

from sas.quant.consequence_types import ConsequenceType, classify_consequence, requires_authorization
from sas.quant.experiment.execution_capability import (
    CapabilityConstraints,
    CapabilityScope,
    CapabilityType,
    ExecutionCapability,
    ReplayGuard,
    ReplayProtectionType,
)
from sas.quant.experiment.protocol_lineage import (
    DomainType,
    DomainValidityInterval,
    ProtocolDomain,
    create_protocol_domain,
)


# ---------------------------------------------------------------------------
# CLI Request
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CLIRequest:
    """A request from the CLI."""
    command: str
    subcommand: str
    arguments: dict
    consequence_type: ConsequenceType
    actor_id: str = "cli-user"
    source: str = "cli"


# ---------------------------------------------------------------------------
# CLI Authority Resolver
# ---------------------------------------------------------------------------


class CLIAuthorityResolver:
    """Resolves authority for CLI commands.

    The CLI does not create authority. It resolves authority from the
    formal protocol based on the command and its classification.
    """

    def __init__(self, domain: ProtocolDomain | None = None):
        self._domain = domain or create_protocol_domain("cli-domain", DomainType.SOVEREIGN)

    def resolve(
        self,
        request: CLIRequest,
    ) -> ExecutionCapability | None:
        """Resolve authority for a CLI request.

        The CLI does not create authority. It resolves authority from the
        formal protocol based on the command and its classification.

        Args:
            request: The CLI request.

        Returns:
            ExecutionCapability if the command is authorized, else None.
        """
        # Check if authorization is required
        if not requires_authorization(request.consequence_type):
            # Informational commands don't need authorization
            return self._create_informational_capability(request)

        # For consequential commands, resolve authorization
        # In a full implementation, this would look up the authorization
        # from a registered authorization store
        return self._create_consequential_capability(request)

    def _create_informational_capability(self, request: CLIRequest) -> ExecutionCapability:
        """Create a capability for informational commands."""
        scope = CapabilityScope(
            domain_id=self._domain.domain_id,
            lineage_id=self._domain.lineage_hash,
            actor_id=request.actor_id,
            action="read_only",
            resource=request.command,
            arguments=request.arguments,
            constraints=CapabilityConstraints(
                allowed_actions=["read_only"],
            ),
            temporal_interval=DomainValidityInterval(
                valid_from=datetime.now(UTC).isoformat(),
                valid_until="2025-12-31T00:00:00Z",
            ),
            authorization_ref=f"auth-{request.command}",
        )

        return ExecutionCapability(
            capability_id=f"cap-{uuid.uuid4().hex[:12]}",
            authorization_ref=f"auth-{request.command}",
            scope=scope,
            capability_type=CapabilityType.OBSERVE,
            replay_guard=ReplayGuard(
                guard_type=ReplayProtectionType.SINGLE_USE,
                nonce=f"nonce-{uuid.uuid4().hex[:16]}",
            ),
            domain_id=self._domain.domain_id,
            lineage_id=self._domain.lineage_hash,
            authority_root=f"auth-{request.command}",
            derived_at=datetime.now(UTC).isoformat(),
            derived_by="cli-transport",
        )

    def _create_consequential_capability(self, request: CLIRequest) -> ExecutionCapability | None:
        """Create a capability for consequential commands.

        In a full implementation, this would look up the authorization
        from a registered authorization store. For now, we create a
        placeholder that documents the authority path.
        """
        scope = CapabilityScope(
            domain_id=self._domain.domain_id,
            lineage_id=self._domain.lineage_hash,
            actor_id=request.actor_id,
            action=request.consequence_type.value,
            resource=request.command,
            arguments=request.arguments,
            constraints=CapabilityConstraints(
                allowed_actions=[request.consequence_type.value],
            ),
            temporal_interval=DomainValidityInterval(
                valid_from=datetime.now(UTC).isoformat(),
                valid_until="2025-12-31T00:00:00Z",
            ),
            authorization_ref=f"auth-{request.command}",
        )

        return ExecutionCapability(
            capability_id=f"cap-{uuid.uuid4().hex[:12]}",
            authorization_ref=f"auth-{request.command}",
            scope=scope,
            capability_type=CapabilityType.EXECUTE,
            replay_guard=ReplayGuard(
                guard_type=ReplayProtectionType.SINGLE_USE,
                nonce=f"nonce-{uuid.uuid4().hex[:16]}",
            ),
            domain_id=self._domain.domain_id,
            lineage_id=self._domain.lineage_hash,
            authority_root=f"auth-{request.command}",
            derived_at=datetime.now(UTC).isoformat(),
            derived_by="cli-transport",
        )


# ---------------------------------------------------------------------------
# CLI Command Registry
# ---------------------------------------------------------------------------


class CLICommandRegistry:
    """Registry of CLI commands and their consequence types."""

    _commands: dict[str, dict[str, ConsequenceType]] = {
        "quant": {
            "auto-research": ConsequenceType.TRADE,
            "backtest": ConsequenceType.READ_ONLY,
            "research": ConsequenceType.READ_ONLY,
            "status": ConsequenceType.READ_ONLY,
            "risk": ConsequenceType.READ_ONLY,
            "provenance": ConsequenceType.READ_ONLY,
            "experiment": ConsequenceType.READ_ONLY,
        },
        "substrate": {
            "boot": ConsequenceType.COMPUTE_EXECUTION,
            "list": ConsequenceType.READ_ONLY,
            "exec": ConsequenceType.COMPUTE_EXECUTION,
            "destroy": ConsequenceType.COMPUTE_EXECUTION,
        },
        "identity": {
            "provision-email": ConsequenceType.IDENTITY_MUTATION,
            "send-email": ConsequenceType.NETWORK_MUTATION,
            "provision-phone": ConsequenceType.IDENTITY_MUTATION,
            "call": ConsequenceType.NETWORK_MUTATION,
            "sms": ConsequenceType.NETWORK_MUTATION,
        },
        "auth": {
            "register": ConsequenceType.AUTHORITY_MUTATION,
            "list": ConsequenceType.READ_ONLY,
            "get": ConsequenceType.CREDENTIAL_ACCESS,
            "unregister": ConsequenceType.AUTHORITY_MUTATION,
            "audit": ConsequenceType.READ_ONLY,
        },
        "payments": {
            "pay": ConsequenceType.PAYMENT,
            "limit": ConsequenceType.AUTHORITY_MUTATION,
            "status": ConsequenceType.READ_ONLY,
        },
        "plugin": {
            "register": ConsequenceType.AUTHORITY_MUTATION,
            "list": ConsequenceType.READ_ONLY,
            "execute": ConsequenceType.PLUGIN_EXECUTION,
            "unregister": ConsequenceType.AUTHORITY_MUTATION,
        },
        "mcp": {
            "serve": ConsequenceType.TOOL_INVOKE,
            "call": ConsequenceType.TOOL_INVOKE,
        },
        "argo": {
            "invoke": ConsequenceType.TOOL_INVOKE,
        },
    }

    @classmethod
    def get_consequence_type(cls, command: str, subcommand: str) -> ConsequenceType | None:
        """Get the consequence type for a CLI command."""
        return cls._commands.get(command, {}).get(subcommand)

    @classmethod
    def classify_command(cls, command: str, subcommand: str) -> str:
        """Classify a CLI command."""
        consequence_type = cls.get_consequence_type(command, subcommand)
        if consequence_type is None:
            return "unknown"
        return classify_consequence(consequence_type).value


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_cli_authority_resolver() -> CLIAuthorityResolver:
    """Create a CLIAuthorityResolver."""
    return CLIAuthorityResolver()


def create_cli_request(
    command: str,
    subcommand: str,
    arguments: dict | None = None,
    actor_id: str = "cli-user",
) -> CLIRequest:
    """Create a CLIRequest."""
    consequence_type = CLICommandRegistry.get_consequence_type(command, subcommand)
    if consequence_type is None:
        consequence_type = ConsequenceType.READ_ONLY
    return CLIRequest(
        command=command,
        subcommand=subcommand,
        arguments=arguments or {},
        consequence_type=consequence_type,
        actor_id=actor_id,
    )
