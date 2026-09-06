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
    KnowledgeGraph,
    MarkdownParser,
    GraphMaterializer,
    Node,
    Edge,
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
from sas.layers.substrate import (
    ComputeSubstrate,
    LocalDockerSubstrate,
    Machine,
    Output,
    Screenshot,
    SubstrateError,
)

from sas.layers.registry import LayerRegistry

__all__ = [
    # Layer 1: Model
    "ModelProvider",
    "ModelIdentity",
    "ModelLocation",
    "Message",
    "Tool",
    "Completion",
    "Token",
    # Layer 2: Harness
    "Harness",
    "Session",
    "Skill",
    "Experience",
    "Context",
    "Result",
    # Layer 3: Compute Substrate
    "ComputeSubstrate",
    "LocalDockerSubstrate",
    "Machine",
    "Screenshot",
    "Output",
    "SubstrateError",
    # Layer 4: Identity
    "EmailIdentity",
    "PhoneIdentity",
    "Inbox",
    "PhoneNumber",
    # Layer 5: Short-Term Memory
    "ShortTermMemory",
    "Fact",
    "Observation",
    "Summary",
    # Layer 6: Long-Term Knowledge
    "CompileTimeKnowledge",
    "KnowledgeGraph",
    "Node",
    "Edge",
    "ParsedResult",
    "MarkdownParser",
    "GraphMaterializer",
    "Diff",
    "AuditReport",
    # Layer 7: Auth
    "AuthBroker",
    "Credentials",
    "Request",
    "Response",
    "AuditEntry",
    "AuditTrail",
    "LocalAuthBroker",
    # Layer 8: Payments
    "PaymentAdapter",
    "PaymentRequirement",
    "Receipt",
    "SpendingLimit",
    # Registry
    "LayerRegistry",
]
