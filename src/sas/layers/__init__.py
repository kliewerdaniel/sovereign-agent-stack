# ── Sovereignty Layers — protocols + registry ─────────────────────────────────

# Each file in this package declares one layer's Protocol class and its
# supporting datatypes. The registry (``LayerRegistry``) is the single
# source of truth for the 8 layer IDs and wires them to the scorer.

from sas.layers.auth import (
    AuditEntry,
    AuditTrail,
    AuthBroker,
    Credentials,
    LocalAuthBroker,
    Request,
    Response,
)
from sas.layers.harness import (
    Context,
    Experience,
    Harness,
    Result,
    Session,
    Skill,
)
from sas.layers.identity import (
    EmailIdentity,
    Inbox,
    PhoneIdentity,
    PhoneNumber,
)
from sas.layers.knowledge import (
    AuditReport,
    CompileTimeKnowledge,
    Diff,
    Edge,
    GraphMaterializer,
    KnowledgeGraph,
    MarkdownParser,
    Node,
    ParsedResult,
)
from sas.layers.memory import (
    Fact,
    Observation,
    ShortTermMemory,
    Summary,
)
from sas.layers.model import (
    Completion,
    Message,
    ModelIdentity,
    ModelLocation,
    ModelProvider,
    Token,
    Tool,
)
from sas.layers.payments import (
    PaymentAdapter,
    PaymentRequirement,
    Receipt,
    SpendingLimit,
)
from sas.layers.registry import LayerRegistry
from sas.layers.substrate import (
    ComputeSubstrate,
    LocalDockerSubstrate,
    Machine,
    Output,
    Screenshot,
    SubstrateError,
)

__all__ = [
    "AuditEntry",
    "AuditReport",
    "AuditTrail",
    # Layer 7: Auth
    "AuthBroker",
    # Layer 6: Long-Term Knowledge
    "CompileTimeKnowledge",
    "Completion",
    # Layer 3: Compute Substrate
    "ComputeSubstrate",
    "Context",
    "Credentials",
    "Diff",
    "Edge",
    # Layer 4: Identity
    "EmailIdentity",
    "Experience",
    "Fact",
    "GraphMaterializer",
    # Layer 2: Harness
    "Harness",
    "Inbox",
    "KnowledgeGraph",
    # Registry
    "LayerRegistry",
    "LocalAuthBroker",
    "LocalDockerSubstrate",
    "Machine",
    "MarkdownParser",
    "Message",
    "ModelIdentity",
    "ModelLocation",
    # Layer 1: Model
    "ModelProvider",
    "Node",
    "Observation",
    "Output",
    "ParsedResult",
    # Layer 8: Payments
    "PaymentAdapter",
    "PaymentRequirement",
    "PhoneIdentity",
    "PhoneNumber",
    "Receipt",
    "Request",
    "Response",
    "Result",
    "Screenshot",
    "Session",
    # Layer 5: Short-Term Memory
    "ShortTermMemory",
    "Skill",
    "SpendingLimit",
    "SubstrateError",
    "Summary",
    "Token",
    "Tool",
]
