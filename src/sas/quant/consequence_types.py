"""Consequence type system — classifies every effect in SAS.

A trade, payment, credential access, identity mutation, process execution,
filesystem mutation, network request, tool invocation, or compute operation
may have completely different implementation semantics, but they share the
same authority derivation semantics.

Architectural law:
    CONSEQUENTIALITY IS A PROTOCOL PROPERTY, NOT A SUBSYSTEM PROPERTY.
"""

from __future__ import annotations

from enum import Enum


class ConsequenceType(str, Enum):
    """Types of consequential effects.

    Every consequential operation in SAS must be classified into one of
    these types. The type determines the authority requirements and the
    verification semantics.

    The authority derivation is identical regardless of type:
        AuthorizationArtifact → ExecutionCapability → CapabilityVerifier → Executor

    The difference is in what the capability binds to and what the executor
    actually does.
    """

    # --- External-consequential ---
    # Can affect something outside the immediate reasoning process.

    TOOL_INVOKE = "tool_invoke"
    """Invocation of a registered tool handler."""

    TRADE = "trade"
    """Financial order submission to a broker."""

    PAYMENT = "payment"
    """Financial transaction (card, MPP, etc.)."""

    IDENTITY_MUTATION = "identity_mutation"
    """Creation, modification, or revocation of an identity."""

    CREDENTIAL_ACCESS = "credential_access"
    """Retrieval or use of stored credentials."""

    SUBPROCESS_EXECUTION = "subprocess_execution"
    """Execution of a host process."""

    COMPUTE_EXECUTION = "compute_execution"
    """Execution of a command in a compute substrate (container, VM)."""

    FILESYSTEM_MUTATION = "filesystem_mutation"
    """Writing, deleting, or mutating filesystem state."""

    NETWORK_MUTATION = "network_mutation"
    """Sending data over the network (API calls, email, SMS)."""

    PLUGIN_EXECUTION = "plugin_execution"
    """Execution of plugin code."""

    AUTHORITY_MUTATION = "authority_mutation"
    """Creation, modification, or revocation of authority (delegation, revocation, policy change)."""

    # --- State-transforming ---
    # Changes local protocol state.

    PROVENANCE_RECORD = "provenance_record"
    """Appending to the provenance graph."""

    KNOWLEDGE_MUTATION = "knowledge_mutation"
    """Modifying the knowledge graph."""

    SESSION_MUTATION = "session_mutation"
    """Modifying session state."""

    # --- Informational ---
    # No persistent or external effect.

    READ_ONLY = "read_only"
    """Read-only query with no side effects."""


class ConsequenceClass(str, Enum):
    """Classification of consequence severity.

    Used to determine authority requirements.
    """

    INFORMATIONAL = "informational"
    """No authority required."""

    STATE_TRANSFORMING = "state_transforming"
    """Authorization required, scope is internal."""

    EXTERNAL_CONSEQUENTIAL = "external_consequential"
    """Full authorization + capability + verification + receipt + provenance."""

    AUTHORITY_MANAGEMENT = "authority_management"
    """HIGHEST — must itself be authorized, must not be self-authorizing."""


# ---------------------------------------------------------------------------
# Mapping from type to class
# ---------------------------------------------------------------------------

CONSEQUENCE_CLASSIFICATION: dict[ConsequenceType, ConsequenceClass] = {
    # External-consequential
    ConsequenceType.TOOL_INVOKE: ConsequenceClass.EXTERNAL_CONSEQUENTIAL,
    ConsequenceType.TRADE: ConsequenceClass.EXTERNAL_CONSEQUENTIAL,
    ConsequenceType.PAYMENT: ConsequenceClass.EXTERNAL_CONSEQUENTIAL,
    ConsequenceType.IDENTITY_MUTATION: ConsequenceClass.EXTERNAL_CONSEQUENTIAL,
    ConsequenceType.CREDENTIAL_ACCESS: ConsequenceClass.EXTERNAL_CONSEQUENTIAL,
    ConsequenceType.SUBPROCESS_EXECUTION: ConsequenceClass.EXTERNAL_CONSEQUENTIAL,
    ConsequenceType.COMPUTE_EXECUTION: ConsequenceClass.EXTERNAL_CONSEQUENTIAL,
    ConsequenceType.FILESYSTEM_MUTATION: ConsequenceClass.EXTERNAL_CONSEQUENTIAL,
    ConsequenceType.NETWORK_MUTATION: ConsequenceClass.EXTERNAL_CONSEQUENTIAL,
    ConsequenceType.PLUGIN_EXECUTION: ConsequenceClass.EXTERNAL_CONSEQUENTIAL,
    ConsequenceType.AUTHORITY_MUTATION: ConsequenceClass.AUTHORITY_MANAGEMENT,
    # State-transforming
    ConsequenceType.PROVENANCE_RECORD: ConsequenceClass.STATE_TRANSFORMING,
    ConsequenceType.KNOWLEDGE_MUTATION: ConsequenceClass.STATE_TRANSFORMING,
    ConsequenceType.SESSION_MUTATION: ConsequenceClass.STATE_TRANSFORMING,
    # Informational
    ConsequenceType.READ_ONLY: ConsequenceClass.INFORMATIONAL,
}


def classify_consequence(consequence_type: ConsequenceType) -> ConsequenceClass:
    """Classify a consequence type."""
    return CONSEQUENCE_CLASSIFICATION.get(consequence_type, ConsequenceClass.EXTERNAL_CONSEQUENTIAL)


def requires_authorization(consequence_type: ConsequenceType) -> bool:
    """Check if a consequence type requires authorization."""
    classification = classify_consequence(consequence_type)
    return classification in (
        ConsequenceClass.STATE_TRANSFORMING,
        ConsequenceClass.EXTERNAL_CONSEQUENTIAL,
        ConsequenceClass.AUTHORITY_MANAGEMENT,
    )


def requires_capability_verification(consequence_type: ConsequenceType) -> bool:
    """Check if a consequence type requires capability verification."""
    classification = classify_consequence(consequence_type)
    return classification in (
        ConsequenceClass.EXTERNAL_CONSEQUENTIAL,
        ConsequenceClass.AUTHORITY_MANAGEMENT,
    )


def requires_receipt(consequence_type: ConsequenceType) -> bool:
    """Check if a consequence type requires an execution receipt."""
    classification = classify_consequence(consequence_type)
    return classification in (
        ConsequenceClass.EXTERNAL_CONSEQUENTIAL,
        ConsequenceClass.AUTHORITY_MANAGEMENT,
    )
